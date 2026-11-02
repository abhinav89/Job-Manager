"""Docker isolation, or explicitly selected trusted local development execution."""
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

_slots = threading.BoundedSemaphore(2)
MAX_RESPONSE = 24 * 1024 * 1024


class SandboxUnavailable(RuntimeError):
    pass


def execution_backend() -> str:
    backend = os.getenv("EXECUTION_BACKEND", "docker").strip().lower()
    if backend not in {"docker", "local"}:
        raise SandboxUnavailable("EXECUTION_BACKEND must be docker or local.")
    if backend == "local" and os.getenv("ENVIRONMENT", "development").strip().lower() != "development":
        raise SandboxUnavailable("Local execution is available only in development. Use Docker for hosted deployments.")
    return backend


def run_isolated(mode: str, payload: dict, timeout: int) -> dict:
    """Run the selected backend; explicit local mode is not isolated."""
    backend = execution_backend()
    if backend == "local":
        if not _slots.acquire(blocking=False):
            raise SandboxUnavailable("The local executor is busy. Please try again shortly.")
        try:
            from services.local_executor import run_local
            return run_local(mode, payload, timeout)
        finally:
            _slots.release()
    docker = shutil.which("docker")
    if not docker or not _slots.acquire(blocking=False):
        raise SandboxUnavailable("The isolated executor is unavailable or busy. Please try again later.")
    name = "cv-tailor-" + uuid.uuid4().hex
    process = None
    try:
        image = os.getenv("PDF_SANDBOX_IMAGE" if mode == "pdf" else "CODE_SANDBOX_IMAGE",
                          "cv-tailor-pdf:1" if mode == "pdf" else "cv-tailor-python:1")
        command = [docker, "run", "--rm", "--pull=never", "--name", name, "--network=none",
                   "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                   "--pids-limit=32", "--memory=512m", "--memory-swap=512m", "--cpus=1",
                   "--user=65534:65534", "--log-driver=none", "--ulimit=nofile=64:64",
                   "--tmpfs=/tmp:rw,noexec,nosuid,size=128m,mode=1777", "--workdir=/tmp", "-i", image]
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors, tempfile.TemporaryFile() as source:
            source.write(json.dumps({**payload, "mode": mode, "timeout": timeout}).encode("utf-8"))
            source.seek(0)
            process = subprocess.Popen(command, stdin=source, stdout=output, stderr=errors)
            deadline = time.monotonic() + timeout + 10
            while process.poll() is None:
                if time.monotonic() > deadline:
                    raise TimeoutError("Isolated execution exceeded its time limit.")
                if os.fstat(output.fileno()).st_size + os.fstat(errors.fileno()).st_size > MAX_RESPONSE:
                    raise ValueError("Isolated execution exceeded its output limit.")
                time.sleep(0.02)
            output.seek(0)
            raw = output.read(MAX_RESPONSE + 1)
            if process.returncode != 0:
                raise SandboxUnavailable("The isolated executor could not start. Build the configured sandbox image and check Docker.")
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Isolated execution exceeded its output limit.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("Invalid executor response.")
            return result
    except (OSError, BrokenPipeError) as exc:
        raise SandboxUnavailable("The isolated executor is unavailable. Host execution is disabled.") from exc
    finally:
        # Removing the container kills all descendants, including those that outlive
        # their parent. No source, secret, host mount, or Docker socket enters it.
        try:
            subprocess.run([docker, "rm", "--force", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        _slots.release()
