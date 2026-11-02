"""Fixed container entry point. Never installed or executed as a host fallback."""
import base64
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time


def main():
    payload = json.load(sys.stdin)
    mode = payload["mode"]
    timeout = min(int(payload["timeout"]), 120)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout + 1))
    start = time.monotonic()
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        if mode == "python":
            source = work / "main.py"
            source.write_text(payload["code"], encoding="utf-8")
            command = [sys.executable, "-I", str(source)]
            limit = 1024 * 1024
        elif mode == "pdf":
            source = work / "resume.tex"
            source.write_text(payload["latex"], encoding="utf-8")
            engine = payload.get("engine", "tectonic")
            if engine == "tectonic":
                command = ["tectonic", "--untrusted", "--only-cached", "--outdir", ".", source.name]
            elif engine == "xelatex":
                command = ["xelatex", "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
                           "-output-directory", ".", source.name]
            else:
                raise ValueError("Unsupported PDF engine.")
            limit = 16 * 1024 * 1024
        else:
            raise ValueError("Unsupported executor mode.")
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(work), "TMPDIR": "/tmp",
               "TECTONIC_CACHE_DIR": "/opt/tectonic-cache", "XDG_CACHE_HOME": "/opt/tex-cache", "LANG": "C.UTF-8",
               "openin_any": "p", "openout_any": "p", "shell_escape": "f"}
        with (work / "stdout").open("w+b") as out, (work / "stderr").open("w+b") as err:
            process = subprocess.Popen(command, cwd=work, env=env, stdin=subprocess.PIPE, stdout=out, stderr=err)
            try:
                process.communicate(payload.get("stdin", "").encode("utf-8"), timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                timed_out = True
            out.seek(0)
            err.seek(0)
            stdout = out.read(limit).decode("utf-8", errors="replace")
            stderr = err.read(limit).decode("utf-8", errors="replace")
        if mode == "python":
            result = {"stdout": stdout, "stderr": "Execution timed out." if timed_out else stderr,
                      "execution_time_ms": int((time.monotonic() - start) * 1000), "timed_out": timed_out}
        else:
            pdf = work / "resume.pdf"
            if timed_out or process.returncode != 0 or not pdf.is_file() or pdf.stat().st_size > limit:
                result = {"error": "LaTeX compilation timed out." if timed_out else (stdout + stderr)[-8000:] or "No valid PDF was produced."}
            else:
                result = {"pdf_b64": base64.b64encode(pdf.read_bytes()).decode("ascii")}
        print(json.dumps(result))


if __name__ == "__main__":
    main()
