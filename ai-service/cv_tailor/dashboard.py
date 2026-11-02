"""Optional dashboard installation and the single-process local launcher."""
from pathlib import Path
import os
import shutil
import subprocess
import sys


def assets_dir():
    return Path(__file__).resolve().parent / "static" / "dashboard"


def repository():
    root = Path(__file__).resolve().parents[2]
    if not root.joinpath("frontend", "package.json").exists():
        raise RuntimeError("Dashboard installation requires the cloned CV Tailor repository.")
    return root


def install():
    root = repository()
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        raise RuntimeError("Install Node.js 22 or newer to build the optional dashboard, then run cv-tailor dashboard install again.")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(root / "ai-service") + "[dashboard]"], check=True, stdout=sys.stderr)
    subprocess.run([npm, "ci"], cwd=root / "frontend", check=True, stdout=sys.stderr)
    subprocess.run([npm, "run", "build"], cwd=root / "frontend", check=True, stdout=sys.stderr)
    return package_assets()


def package_assets():
    source, destination = repository() / "frontend" / "out", assets_dir()
    if not source.joinpath("index.html").exists():
        raise RuntimeError("Dashboard static export did not produce index.html")
    assert destination.resolve().is_relative_to(Path(__file__).resolve().parent / "static")
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return {"installed": True, "assets": str(destination), "next": "cv-tailor dashboard"}


def start(port=8000, open_browser=True):
    if not assets_dir().joinpath("index.html").exists():
        raise RuntimeError("Dashboard not installed. Run cv-tailor dashboard install first.")
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    import uvicorn
    if open_browser:
        import threading, webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()
    from cv_tailor.main import app
    uvicorn.run(app, host="127.0.0.1", port=port, proxy_headers=False)
