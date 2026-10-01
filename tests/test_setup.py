from pathlib import Path
from unittest.mock import MagicMock, patch
import importlib
import sys


def test_directories_exist():
    base = Path(__file__).resolve().parent.parent
    for sub in ("ui", "services", "pipeline", "db", "ai", "storage", "config"):
        assert (base / "src" / sub).is_dir()
    assert (base / "data" / "assets").is_dir()
    assert (base / "data" / "uploads").is_dir()


def test_requirements_txt_has_dependencies():
    base = Path(__file__).resolve().parent.parent
    content = (base / "requirements.txt").read_text()
    for dep in ("flet", "peewee", "PyMuPDF", "pdfplumber", "Pillow",
                "opencv-python", "openai", "google-generativeai",
                "anthropic", "keyring", "requests", "pytest"):
        assert dep in content, f"Missing dependency: {dep}"


def test_main_module_imports():
    for mod_name in list(sys.modules):
        if mod_name in ("main", "src.main"):
            del sys.modules[mod_name]
    mod = importlib.import_module("main")
    assert hasattr(mod, "main")
    assert callable(mod.main)


def test_main_creates_data_dirs(tmp_path, monkeypatch):
    import main as main_mod
    fake_data = tmp_path / "data"
    monkeypatch.setattr(main_mod, "DATA_DIR", fake_data)
    monkeypatch.setattr(main_mod, "ASSETS_DIR", fake_data / "assets")
    monkeypatch.setattr(main_mod, "UPLOADS_DIR", fake_data / "uploads")
    main_mod._ensure_dirs()
    assert fake_data.exists()
    assert (fake_data / "assets").exists()
    assert (fake_data / "uploads").exists()


def test_app_shell_has_five_nav_destinations():
    import main as main_mod
    fake_page = MagicMock()
    with patch("src.services.workspace_service.WorkspaceService.list_all", return_value=[]), \
         patch("src.services.workspace_service.WorkspaceService.get_active", return_value=None):
        shell = main_mod.AppShell(fake_page)
    assert len(shell.rail.destinations) == 5
    labels = [d.label for d in shell.rail.destinations]
    assert labels == ["Workspaces", "Provas", "Questões", "Tópicos", "Configurações"]
