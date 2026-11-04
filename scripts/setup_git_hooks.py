"""Enable this repository's branch guards without changing global Git settings."""
from pathlib import Path
import subprocess


def configure_hooks(root):
    root = Path(root).resolve()
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)

    current = git("config", "--get", "core.hooksPath").stdout.strip()
    if current == ".githooks":
        print("Repository branch guards are already enabled.")
        return
    hooks = git("rev-parse", "--git-path", "hooks")
    if hooks.returncode:
        raise RuntimeError("Run this setup from a Git checkout of CV Tailor.")
    previous = root / hooks.stdout.strip()
    active_hooks = previous.is_dir() and any(path.is_file() and not path.name.endswith(".sample") for path in previous.iterdir())
    if current or active_hooks:
        raise RuntimeError("Existing Git hooks were left unchanged. Integrate .githooks guards with that setup.")
    if not all((root / ".githooks" / name).is_file() for name in ("pre-commit", "pre-push")):
        raise RuntimeError("The repository's .githooks files are missing.")
    result = git("config", "--local", "core.hooksPath", ".githooks")
    if result.returncode:
        raise RuntimeError("Could not enable the repository's Git hooks.")
    print("Repository branch guards enabled: develop on dev; merge to main through a PR.")


if __name__ == "__main__":
    try:
        configure_hooks(Path(__file__).resolve().parents[1])
    except RuntimeError as error:
        raise SystemExit(str(error))
