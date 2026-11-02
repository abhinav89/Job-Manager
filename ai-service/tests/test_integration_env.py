"""Credential persistence is local, Git-ignored, and never echoed by the wizard."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import warnings

from dotenv import dotenv_values
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "integration_env.py"
spec = importlib.util.spec_from_file_location("integration_env", SCRIPT)
integration_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration_env)


@pytest.fixture
def checkout(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env.*\n", encoding="utf-8")
    return tmp_path


def test_values_roundtrip_without_interpolation_and_preserve_other_keys(checkout, capsys):
    target = checkout / ".env.integrations"
    target.write_text("# Keep this comment\nCV_TAILOR_EXISTING='saved'\n", encoding="utf-8")
    value = "fictional 'quoted' \\ path ${HOME}\nsecond line"
    assert integration_env.save_env_values({"CV_TAILOR_TEST_VALUE": value}, checkout) == ["CV_TAILOR_TEST_VALUE"]
    assert dotenv_values(target, interpolate=False) == {"CV_TAILOR_EXISTING": "saved", "CV_TAILOR_TEST_VALUE": value}
    assert "# Keep this comment" in target.read_text(encoding="utf-8")
    assert integration_env.configured_keys(checkout) == ["CV_TAILOR_EXISTING", "CV_TAILOR_TEST_VALUE"]
    assert not list(checkout.glob(".env.integrations.*"))
    captured = capsys.readouterr()
    assert not captured.out and not captured.err


def test_tracked_environment_file_is_refused_even_when_ignored(checkout):
    target = checkout / ".env.integrations"
    target.write_text("existing\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(checkout), "add", "--force", ".env.integrations"], check=True)
    with pytest.raises(integration_env.CredentialSetupError, match="already tracked"):
        integration_env.save_env_values({"CV_TAILOR_TEST": "fictional"}, checkout)
    assert target.read_text(encoding="utf-8") == "existing\n"


def test_unignored_environment_file_is_refused_without_writing(checkout):
    (checkout / ".gitignore").write_text("", encoding="utf-8")
    with pytest.raises(integration_env.CredentialSetupError, match="gitignore"):
        integration_env.save_env_values({"CV_TAILOR_TEST": "fictional"}, checkout)
    assert not (checkout / ".env.integrations").exists()


def test_symlink_cannot_redirect_credential_writes(checkout, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "target"
    outside.write_text("untouched", encoding="utf-8")
    try:
        (checkout / ".env.integrations").symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks requires OS permission")
    with pytest.raises(integration_env.CredentialSetupError, match="regular file"):
        integration_env.save_env_values({"CV_TAILOR_TEST": "fictional"}, checkout)
    assert outside.read_text(encoding="utf-8") == "untouched"


@pytest.mark.parametrize("key,value", [("PATH", "fictional"), ("CV_TAILOR_TEST\nOTHER", "fictional"), ("CV_TAILOR_TEST", ""), ("CV_TAILOR_TEST", None)])
def test_invalid_keys_or_values_never_write(checkout, key, value):
    with pytest.raises(integration_env.CredentialSetupError):
        integration_env.save_env_values({key: value}, checkout)
    assert not (checkout / ".env.integrations").exists()


def test_status_reports_names_without_values(checkout, monkeypatch, capsys):
    integration_env.save_env_values({"CV_TAILOR_TEST": "fictional-private-value"}, checkout)
    monkeypatch.setattr(integration_env, "ROOT", checkout)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "status"])
    assert integration_env.main() == 0
    output = capsys.readouterr()
    assert "CV_TAILOR_TEST" in output.out
    assert "fictional-private-value" not in output.out + output.err


def test_noninteractive_input_is_refused_before_asking_for_credentials(checkout, monkeypatch, capsys):
    monkeypatch.setattr(integration_env, "ROOT", checkout)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "set", "CV_TAILOR_TEST"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(integration_env.getpass, "getpass", lambda *args: pytest.fail("must not request input"))
    assert integration_env.main() == 1
    assert "own terminal" in capsys.readouterr().err
    assert not (checkout / ".env.integrations").exists()


def test_hidden_input_saves_without_echo_and_enter_keeps_saved_value(checkout, monkeypatch, capsys):
    monkeypatch.setattr(integration_env, "ROOT", checkout)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "set", "CV_TAILOR_TEST"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(integration_env.getpass, "getpass", lambda *args: "fictional-private-value")
    assert integration_env.main() == 0
    monkeypatch.setattr(integration_env.getpass, "getpass", lambda *args: "")
    assert integration_env.main() == 0
    assert dotenv_values(checkout / ".env.integrations", interpolate=False)["CV_TAILOR_TEST"] == "fictional-private-value"
    output = capsys.readouterr()
    assert "CV_TAILOR_TEST" in output.out
    assert "fictional-private-value" not in output.out + output.err


def test_getpass_cannot_fall_back_to_echoing_input(checkout, monkeypatch, capsys):
    monkeypatch.setattr(integration_env, "ROOT", checkout)
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "set", "CV_TAILOR_TEST"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    def echo_fallback(*args):
        warnings.warn("input could echo", integration_env.getpass.GetPassWarning)
        pytest.fail("warning must stop input before the echoing fallback")

    monkeypatch.setattr(integration_env.getpass, "getpass", echo_fallback)
    assert integration_env.main() == 1
    assert "Hidden input is unavailable" in capsys.readouterr().err
    assert not (checkout / ".env.integrations").exists()


def test_bad_arguments_are_not_echoed(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "fictional-private-value"])
    with pytest.raises(SystemExit):
        integration_env.main()
    assert "fictional-private-value" not in capsys.readouterr().err
