"""Run with Python 3.12+: python scripts/install.py [--cli-only|--with-dashboard]."""
import argparse
from pathlib import Path
import os
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description="Install CV Tailor locally")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--cli-only", action="store_true")
    modes.add_argument("--with-dashboard", action="store_true")
    parser.add_argument("--data-dir")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        parser.error("Python 3.12 or newer is required")
    dashboard = args.with_dashboard
    if not args.cli_only and not args.with_dashboard and sys.stdin.isatty():
        dashboard = input("Install: [1] CLI only (default)  [2] CLI + dashboard: ").strip() == "2"
    root = Path(__file__).resolve().parents[1]
    environment = root / ".venv"
    interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.exists():
        venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run([str(interpreter), "-m", "pip", "install", "-e", str(root / "ai-service")], check=True)
    prefix = [str(interpreter), "-m", "cv_tailor"]
    if args.data_dir:
        prefix += ["--data-dir", args.data_dir]
    subprocess.run(prefix + ["init"], check=True)
    if dashboard:
        subprocess.run(prefix + ["dashboard", "install"], check=True)
    command = environment / ("Scripts/cv-tailor.exe" if os.name == "nt" else "bin/cv-tailor")
    print(f"\nInstalled. Command: {command}\nOpen your AI agent in {root}.\nAdd the dashboard anytime: {command} dashboard install")


if __name__ == "__main__":
    main()
