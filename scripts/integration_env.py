"""Human-run hidden credential entry for agent-guided tracking integrations.

Only variable names belong on the command line. Values are entered in the user's
terminal or passed in memory by a local OAuth script, never through chat/logs.
"""
import argparse
import getpass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import warnings

from dotenv import dotenv_values, set_key

ROOT = Path(__file__).resolve().parents[1]
ENV_NAME = ".env.integrations"
KEY_PATTERN = re.compile(r"CV_TAILOR_[A-Z][A-Z0-9_]*\Z")


class CredentialSetupError(ValueError):
    pass


def checked_env_path(root=None):
    root = Path(ROOT if root is None else root).resolve()
    target = root / ENV_NAME
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise CredentialSetupError("The integration environment path must be a regular file.")
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", ENV_NAME], capture_output=True)
    if tracked.returncode == 0:
        raise CredentialSetupError("The integration environment file is already tracked by Git. Remove it from tracking before saving credentials.")
    ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet", "--", ENV_NAME], capture_output=True)
    if ignored.returncode != 0:
        raise CredentialSetupError("Add .env.integrations to .gitignore in this checkout before saving credentials.")
    return target


def save_env_values(values, root=None):
    """Save values without logging them; safe to call from a local OAuth wizard."""
    if not values or any(not isinstance(key, str) or not KEY_PATTERN.fullmatch(key) or not isinstance(value, str) or not value for key, value in values.items()):
        raise CredentialSetupError("Use nonempty values and CV_TAILOR_ environment variable names.")
    target = checked_env_path(root)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".env.integrations.", dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        if target.exists():
            shutil.copyfile(target, temporary)
        for key, value in values.items():
            set_key(str(temporary), key, value, quote_mode="always")
        os.chmod(temporary, 0o600)
        checked_env_path(root)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return sorted(values)


def configured_keys(root=None):
    target = checked_env_path(root)
    if not target.exists():
        return []
    return sorted(key for key, value in dotenv_values(target, interpolate=False).items() if KEY_PATTERN.fullmatch(key) and value)


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid arguments. Use --help; only variable names belong on the command line.\n")


def main():
    parser = Arguments(description=__doc__)
    parser.add_argument("action", choices=["set", "status"])
    parser.add_argument("keys", nargs="*")
    args = parser.parse_args()
    try:
        checked_env_path()
        if args.action == "status":
            print("Configured variable names: " + (", ".join(configured_keys()) or "none"))
            return 0
        if not args.keys or any(not KEY_PATTERN.fullmatch(key) for key in args.keys):
            raise CredentialSetupError("Supply CV_TAILOR_ variable names; do not supply their values as arguments.")
        if not sys.stdin.isatty():
            raise CredentialSetupError("Run this command in your own terminal for hidden credential entry. Do not paste credentials into the agent chat.")
        previous = dotenv_values(ROOT / ENV_NAME, interpolate=False) if (ROOT / ENV_NAME).exists() else {}
        values = {}
        for key in args.keys:
            suffix = " (Enter keeps the saved value)" if previous.get(key) else ""
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                value = getpass.getpass(key + suffix + ": ")
            if not value:
                value = previous.get(key)
            if not value:
                raise CredentialSetupError("A required value was empty; no credentials were saved.")
            values[key] = value
        names = save_env_values(values)
        print("Saved variable names to the Git-ignored .env.integrations: " + ", ".join(names))
        return 0
    except CredentialSetupError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except getpass.GetPassWarning:
        print("Hidden input is unavailable in this terminal; no credentials were saved.", file=sys.stderr)
        return 1
    except (ValueError, OSError):
        print("Unable to save integration credentials; check the local environment file and file permissions.", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Credential entry cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
