"""Exercise branch guards against disposable local repositories and remotes."""
import importlib.util
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("setup_git_hooks", ROOT / "scripts/setup_git_hooks.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=check)


@pytest.fixture
def guarded_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "--initial-branch=main")
    git(root, "config", "user.name", "Workflow Test")
    git(root, "config", "user.email", "workflow@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    shutil.copytree(ROOT / ".githooks", root / ".githooks")
    for hook in (root / ".githooks").iterdir():
        hook.chmod(0o755)
    (root / "example.txt").write_text("initial\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initial fixture")
    setup.configure_hooks(root)
    return root


def test_main_commit_is_blocked_but_dev_commit_works(guarded_repo):
    root = guarded_repo
    (root / "example.txt").write_text("changed\n", encoding="utf-8")
    git(root, "add", "example.txt")
    blocked = git(root, "commit", "-m", "Must be blocked", check=False)
    assert blocked.returncode != 0
    assert "main are blocked" in blocked.stderr
    git(root, "switch", "-c", "dev")
    git(root, "commit", "-m", "Development change")
    setup.configure_hooks(root)  # Enabling the same guards again is harmless.


def test_push_guard_checks_destination_including_deletions(guarded_repo, tmp_path):
    root = guarded_repo
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    git(root, "remote", "add", "origin", str(remote))
    git(root, "switch", "-c", "dev")
    git(root, "push", "origin", "dev")
    blocked = git(root, "push", "origin", "dev:main", check=False)
    assert blocked.returncode != 0
    assert "Direct pushes to main are blocked" in blocked.stderr
    sha = git(root, "rev-parse", "HEAD").stdout.strip()
    git(remote, "update-ref", "refs/heads/main", sha)
    blocked = git(root, "push", "origin", ":main", check=False)
    assert blocked.returncode != 0
    assert "Direct pushes to main are blocked" in blocked.stderr


def test_hook_setup_preserves_custom_configuration(guarded_repo):
    git(guarded_repo, "config", "core.hooksPath", "custom-hooks")
    with pytest.raises(RuntimeError, match="left unchanged"):
        setup.configure_hooks(guarded_repo)
    assert git(guarded_repo, "config", "core.hooksPath").stdout.strip() == "custom-hooks"


def test_hook_setup_preserves_other_default_hooks(guarded_repo):
    git(guarded_repo, "config", "--unset", "core.hooksPath")
    previous = guarded_repo / git(guarded_repo, "rev-parse", "--git-path", "hooks").stdout.strip()
    custom = previous / "post-commit"
    custom.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="left unchanged"):
        setup.configure_hooks(guarded_repo)
    assert custom.exists()
    assert git(guarded_repo, "config", "--get", "core.hooksPath", check=False).returncode != 0
