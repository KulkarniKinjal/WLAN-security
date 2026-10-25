import os
import sys
import tempfile
from pathlib import Path

import pytest

# Point the app at an isolated temp DB/data dir before importing it.
_tmp = tempfile.mkdtemp(prefix="attacklab-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["REPORTS_DIR"] = f"{_tmp}/reports"
os.environ["WORDLIST_DIR"] = f"{_tmp}/wordlists"
os.environ["CAPTURE_FIXTURE_DIR"] = f"{_tmp}/captures"
os.environ["EXECUTION_MODE"] = "demonstration"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Path(os.environ["WORDLIST_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["WORDLIST_DIR"], "sample.txt").write_text("password123\nletmein\n")
    init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)
