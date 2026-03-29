from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[5]


def test_api_index_uses_development_root():
    content = (PROJECT_ROOT / "api" / "index.py").read_text()

    assert 'PROJECT_ROOT / "development"' in content
    assert ".gemini" not in content


def test_run_crm_uses_development_root():
    content = (PROJECT_ROOT / "run_crm.sh").read_text()

    assert 'APP_ROOT="$PROJECT_ROOT/development"' in content
    assert 'open "http://127.0.0.1:$PORT" >/dev/null 2>&1 || true' in content
    assert ".gemini/development" not in content


def test_render_uses_development_root_and_repo_requirements():
    content = (PROJECT_ROOT / "render.yaml").read_text()

    assert "rootDir: development" in content
    assert "buildCommand: pip install -r ../requirements.txt" in content
    assert ".gemini/development" not in content


def test_pytest_cache_uses_development_root():
    content = (PROJECT_ROOT / "pytest.ini").read_text()

    assert "cache_dir = development/.pytest_cache" in content
    assert ".gemini/development" not in content


def test_main_app_no_longer_mounts_removed_agent_apps():
    content = (PROJECT_ROOT / "development" / "web" / "backend" / "app" / "main.py").read_text()

    assert 'app.mount("/agent",' not in content
    assert 'app.mount("/agent-gem",' not in content
