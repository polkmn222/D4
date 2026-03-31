import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATABASE_MODULE = "db.database"
MAIN_MODULE = "web.backend.app.main"


def test_database_module_source_defers_runtime_bootstrap_until_explicit_init():
    source = (ROOT / "development" / "db" / "database.py").read_text(encoding="utf-8")

    assert "def initialize_database_runtime(target_engine=None) -> None:" in source
    assert "ensure_runtime_columns(target_engine or engine)" in source
    assert "initialize_database_runtime()" not in source.split("Base = declarative_base()", 1)[0]


def test_main_source_initializes_database_runtime_during_lifespan():
    source = (ROOT / "development" / "web" / "backend" / "app" / "main.py").read_text(encoding="utf-8")

    assert "from db.database import engine, Base, initialize_database_runtime" in source
    assert "Base.metadata.create_all(bind=engine)" in source
    assert "initialize_database_runtime()" in source


def test_database_import_does_not_require_live_postgres_connection():
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql://user:pass@does-not-resolve.invalid:5432/test_db"
    env["PYTHONPATH"] = str(ROOT / "development")

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib; "
                "module = importlib.import_module('db.database'); "
                "print(module.engine.url.drivername)"
            ),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "postgresql+psycopg" in completed.stdout


def test_initialize_database_runtime_runs_bootstrap_once(monkeypatch):
    module = __import__(DATABASE_MODULE, fromlist=["initialize_database_runtime"])
    calls = []

    def fake_ensure_runtime_columns(target_engine=None):
        calls.append(target_engine)

    monkeypatch.setattr(module, "ensure_runtime_columns", fake_ensure_runtime_columns)
    monkeypatch.setattr(module, "_runtime_initialized", False)

    try:
        module.initialize_database_runtime("engine-a")
        module.initialize_database_runtime("engine-b")
    finally:
        monkeypatch.setattr(module, "_runtime_initialized", False)

    assert calls == ["engine-a"]


def test_integration_conftest_initializes_schema_in_session_fixture():
    source = (ROOT / "development" / "test" / "integration" / "conftest.py").read_text(encoding="utf-8")

    assert '@pytest.fixture(scope="session", autouse=True)' in source
    assert "def initialize_postgres_schema(postgres_engine):" in source
    assert "Base.metadata.create_all(bind=postgres_engine)" in source
    assert "initialize_database_runtime(postgres_engine)" in source


def test_test_conftest_preserves_explicit_integration_marks_inside_unit_tree():
    source = (ROOT / "development" / "test" / "conftest.py").read_text(encoding="utf-8")

    assert '"integration" in parts or "integration" in item.keywords' in source
    assert 'elif "unit" in parts and "integration" not in item.keywords:' in source
