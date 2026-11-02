"""Docker-free development execution, with explicit production safeguards."""
import os
import time
import unittest
from unittest.mock import patch

from services.sandbox import SandboxUnavailable, run_isolated


class LocalExecutionTests(unittest.TestCase):
    def test_native_python_uses_stdin_without_docker_or_application_secrets(self):
        with patch.dict(os.environ, {"EXECUTION_BACKEND": "local", "ENVIRONMENT": "development", "AUDIT_SECRET": "private"}), patch("services.sandbox.shutil.which", side_effect=AssertionError("Docker must not be consulted")):
            result = run_isolated("python", {"code": "import os\nprint(input())\nprint(os.getenv('AUDIT_SECRET'))", "stdin": "hello"}, 5)
        self.assertEqual(result["stdout"].splitlines(), ["hello", "None"])
        self.assertFalse(result["timed_out"])

    def test_native_python_times_out_and_bounds_output(self):
        with patch.dict(os.environ, {"EXECUTION_BACKEND": "local", "ENVIRONMENT": "development"}):
            started = time.monotonic()
            result = run_isolated("python", {"code": "import time\ntime.sleep(30)"}, 1)
            self.assertTrue(result["timed_out"])
            self.assertLess(time.monotonic() - started, 8)
            result = run_isolated("python", {"code": "while True: print('x'*10000)"}, 5)
            self.assertLessEqual(len(result["stdout"]), 1024 * 1024)
            self.assertIn("output limit", result["stderr"])

    def test_local_mode_cannot_be_used_in_production(self):
        with patch.dict(os.environ, {"EXECUTION_BACKEND": "local", "ENVIRONMENT": "production"}), patch("services.sandbox.subprocess.Popen") as start:
            with self.assertRaisesRegex(SandboxUnavailable, "development"):
                run_isolated("python", {"code": "print(1)"}, 1)
        start.assert_not_called()

    def test_unknown_backend_is_rejected(self):
        with patch.dict(os.environ, {"EXECUTION_BACKEND": "typo"}):
            with self.assertRaisesRegex(SandboxUnavailable, "EXECUTION_BACKEND"):
                run_isolated("python", {"code": "print(1)"}, 1)

    def test_missing_native_compiler_does_not_fall_back_to_docker(self):
        with patch.dict(os.environ, {"EXECUTION_BACKEND": "local", "ENVIRONMENT": "development"}), patch("services.local_executor.Path.is_file", return_value=False), patch("services.local_executor.shutil.which", return_value=None), patch("services.sandbox.subprocess.Popen") as start:
            with self.assertRaisesRegex(SandboxUnavailable, "Install xelatex"):
                run_isolated("pdf", {"latex": "document", "engine": "xelatex"}, 1)
        start.assert_not_called()
