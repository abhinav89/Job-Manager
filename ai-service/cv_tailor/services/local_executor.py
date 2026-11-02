"""Native tools for trusted, single-user development; this is not a sandbox."""
import base64
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from cv_tailor.services.sandbox import SandboxUnavailable


def _stop(process):
    if os.name == "nt":
        if process.poll() is None:
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run_local(mode: str, payload: dict, timeout: int) -> dict:
    if mode not in {"python", "pdf"}:
        raise ValueError("Unsupported execution mode.")
    limit = 1024 * 1024 if mode == "python" else 16 * 1024 * 1024
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="cv-tailor-local-") as directory:
        work = Path(directory)
        if mode == "python":
            (work / "main.py").write_text(payload["code"], encoding="utf-8")
            command = [sys.executable, "-I", "-u", "main.py"]
        else:
            engine = payload.get("engine", "tectonic")
            if engine not in {"tectonic", "xelatex"}:
                raise ValueError("Unsupported PDF engine.")
            installed = Path(sys.executable).parent / (engine + (".exe" if os.name == "nt" else ""))
            executable = str(installed) if installed.is_file() else shutil.which(engine)
            if not executable:
                raise SandboxUnavailable(f"Install {engine} for native PDF compilation, or select EXECUTION_BACKEND=docker.")
            (work / "resume.tex").write_text(payload["latex"], encoding="utf-8")
            command = [executable, "--untrusted", "--outdir", ".", "resume.tex"] if engine == "tectonic" else [
                executable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", ".", "resume.tex"]
        # Do not hand API keys, database credentials or session secrets to tools.
        allowed = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOME")
        env = {key: os.environ[key] for key in allowed if key in os.environ}
        env.update(TMP=directory, TEMP=directory, TMPDIR=directory, PYTHONIOENCODING="utf-8",
                   openin_any="p", openout_any="p", shell_escape="f")
        options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        with tempfile.TemporaryFile() as source, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            source.write(payload.get("stdin", "").encode("utf-8"))
            source.seek(0)
            try:
                process = subprocess.Popen(command, cwd=work, env=env, stdin=source, stdout=out, stderr=err, **options)
            except OSError as exc:
                raise SandboxUnavailable("The native tool could not start. Check your Python or LaTeX installation.") from exc
            timed_out = exceeded = False
            try:
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    timed_out = time.monotonic() >= deadline
                    exceeded = max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size) > limit
                    if timed_out or exceeded:
                        break
                    time.sleep(.02)
            finally:
                _stop(process)
            out.seek(0)
            err.seek(0)
            stdout, stderr = (stream.read(limit).decode("utf-8", errors="replace") for stream in (out, err))
        error = "Execution timed out." if timed_out else "Execution exceeded its output limit." if exceeded else ""
        if mode == "python":
            return {"stdout": stdout, "stderr": error or stderr, "execution_time_ms": int((time.monotonic() - started) * 1000), "timed_out": timed_out}
        pdf = work / "resume.pdf"
        if error or process.returncode != 0 or not pdf.is_file() or pdf.stat().st_size > limit:
            return {"error": error or (stdout + stderr)[-8000:] or "No valid PDF was produced."}
        return {"pdf_b64": base64.b64encode(pdf.read_bytes()).decode("ascii")}
