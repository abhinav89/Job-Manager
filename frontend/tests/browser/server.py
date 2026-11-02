"""Disposable instance of the packaged dashboard for browser tests."""
from pathlib import Path
import os
import tempfile

with tempfile.TemporaryDirectory(prefix="cv-tailor-browser-") as directory:
    os.environ["CV_TAILOR_HOME"] = directory
    os.environ["AI_MODE"] = "external"
    from cv_tailor.dashboard import package_assets, start
    package_assets()
    try:
        start(port=3218, open_browser=False)
    finally:
        from cv_tailor.database import engine
        engine.dispose()
