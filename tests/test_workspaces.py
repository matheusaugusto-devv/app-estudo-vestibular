import pytest
from unittest.mock import patch

from src.db.connection import database, disconnect
from src.db import init_db
from src.db.models import Exam, Question, Workspace
from src.services.workspace_service import WorkspaceService


@pytest.fixture
def db(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    assets_dir = data_dir / "assets"
    monkeypatch.setattr(
        "src.services.workspace_service.ASSETS_DIR", assets_dir
    )
    db_path = data_dir / "app.db"
    init_db(db_path)
    yield database
    disconnect()
    if not database.is_closed():
        database.close()


class TestCreate:
    def test_create_basic(self, db):
        ws = WorkspaceService.create("ENEM 2024")
        assert ws.id is not None
        assert ws.name == "ENEM 2024"
        assert ws.description is None

    def test_create_with_description(self, db):
        ws = WorkspaceService.create("Concurso BB", "Estudo para Banco do Brasil")
        assert ws.description == "Estudo para Banco do Brasil"

    def test_create_empty_name_raises(self, db):
        with pytest.raises(ValueError, match="obrigatório"):
            WorkspaceService.create("")

    def test_create_whitespace_name_raises(self, db):
        with pytest.raises(ValueError, match="obrigatório"):
            WorkspaceService.create("   ")

    def test_create_duplicate_name_raises(self, db):
        WorkspaceService.create("ENEM 2024")
        with pytest.raises(ValueError, match="Já existe"):
            WorkspaceService.create("ENEM 2024")

    def test_create_name_over_100_chars_raises(self, db):
        with pytest.raises(ValueError, match="100 caracteres"):
            WorkspaceService.create("A" * 101)

    def test_create_description_over_500_chars_raises(self, db):
        with pytest.raises(ValueError, match="500 caracteres"):
            WorkspaceService.create("OK", "B" * 501)

    def test_create_strips_name(self, db):
        ws = WorkspaceService.create("  ENEM  ")
        assert ws.name == "ENEM"

    def test_create_assets_folder(self, db, tmp_path):
        from src.services.workspace_service import ASSETS_DIR
        ws = WorkspaceService.create("WS1")
        assets_path = ASSETS_DIR / str(ws.id)
        assert assets_path.exists()
        assert assets_path.is_dir()

    def test_create_assets_folder_failure_logs_warning(self, db, monkeypatch):
        def _raise(*a, **k):
            raise OSError("disk full")
        monkeypatch.setattr("pathlib.Path.mkdir", _raise)
        ws = WorkspaceService.create("WS1")
        assert ws.id is not None


class TestList:
    def test_list_all_ordered_by_created_desc(self, db):
        ws1 = WorkspaceService.create("Primeiro")
        ws2 = WorkspaceService.create("Segundo")
        ws3 = WorkspaceService.create("Terceiro")
        result = WorkspaceService.list_all()
        assert result[0].name == "Terceiro"
        assert result[1].name == "Segundo"
        assert result[2].name == "Primeiro"

    def test_list_empty(self, db):
        assert WorkspaceService.list_all() == []


class TestUpdate:
    def test_update_name(self, db):
        ws = WorkspaceService.create("ENEM 2024")
        updated = WorkspaceService.update(ws.id, "ENEM 2025")
        assert updated.name == "ENEM 2025"

    def test_update_description(self, db):
        ws = WorkspaceService.create("WS", "old desc")
        updated = WorkspaceService.update(ws.id, "WS", "new desc")
        assert updated.description == "new desc"

    def test_update_empty_name_raises(self, db):
        ws = WorkspaceService.create("WS")
        with pytest.raises(ValueError, match="obrigatório"):
            WorkspaceService.update(ws.id, "")

    def test_update_duplicate_name_raises(self, db):
        WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        with pytest.raises(ValueError, match="Já existe"):
            WorkspaceService.update(ws2.id, "WS1")

    def test_update_same_name_allowed(self, db):
        ws = WorkspaceService.create("WS1", "desc")
        updated = WorkspaceService.update(ws.id, "WS1", "new desc")
        assert updated.name == "WS1"
        assert updated.description == "new desc"


class TestDelete:
    def test_delete_basic(self, db):
        WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        WorkspaceService.delete(ws2.id)
        assert Workspace.select().where(Workspace.id == ws2.id).count() == 0

    def test_delete_last_workspace_raises(self, db):
        WorkspaceService.create("Only")
        with pytest.raises(ValueError, match="único workspace"):
            WorkspaceService.delete(1)

    def test_delete_cascades_exams_questions(self, db):
        from src.db.models import Exam, Question, UserAnswer
        ws1 = WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        exam = Exam.create(workspace=ws2, title="P1", source_pdf_path="/x.pdf")
        q = Question.create(exam=exam, question_number=1, statement="Q", question_type="multiple_choice", options={})
        UserAnswer.create(question=q, user_answer="A", is_correct=True)

        WorkspaceService.delete(ws2.id)

        assert Exam.select().where(Exam.id == exam.id).count() == 0
        assert Question.select().where(Question.id == q.id).count() == 0
        assert UserAnswer.select().count() == 0
        assert Workspace.select().count() == 1

    def test_delete_removes_assets_folder(self, db, tmp_path):
        from src.services.workspace_service import ASSETS_DIR
        ws1 = WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        assets_path = ASSETS_DIR / str(ws2.id)
        assert assets_path.exists()
        WorkspaceService.delete(ws2.id)
        assert not assets_path.exists()

    def test_delete_active_switches_to_remaining(self, db):
        ws1 = WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        WorkspaceService.set_active(ws2.id)
        WorkspaceService.delete(ws2.id)
        from src.config.settings import ConfigService
        active_id = ConfigService.get("default_workspace_id")
        assert int(active_id) == ws1.id


class TestSetActive:
    def test_set_and_get_active(self, db):
        ws1 = WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        WorkspaceService.set_active(ws2.id)
        active = WorkspaceService.get_active()
        assert active.id == ws2.id

    def test_get_active_returns_first_when_none_set(self, db):
        ws1 = WorkspaceService.create("WS1")
        active = WorkspaceService.get_active()
        assert active.id == ws1.id

    def test_get_active_returns_none_when_empty(self, db):
        active = WorkspaceService.get_active()
        assert active is None


class TestGetCounts:
    def test_counts_empty_workspace(self, db):
        ws = WorkspaceService.create("WS")
        exam_count, question_count = WorkspaceService.get_counts(ws.id)
        assert exam_count == 0
        assert question_count == 0

    def test_counts_with_exams_and_questions(self, db):
        ws = WorkspaceService.create("WS")
        exam1 = Exam.create(workspace=ws, title="P1", source_pdf_path="/x.pdf")
        exam2 = Exam.create(workspace=ws, title="P2", source_pdf_path="/y.pdf")
        Question.create(exam=exam1, question_number=1, statement="Q1", question_type="multiple_choice", options={})
        Question.create(exam=exam1, question_number=2, statement="Q2", question_type="multiple_choice", options={})
        Question.create(exam=exam2, question_number=1, statement="Q3", question_type="multiple_choice", options={})
        exam_count, question_count = WorkspaceService.get_counts(ws.id)
        assert exam_count == 2
        assert question_count == 3

    def test_counts_isolated_per_workspace(self, db):
        ws1 = WorkspaceService.create("WS1")
        ws2 = WorkspaceService.create("WS2")
        exam = Exam.create(workspace=ws1, title="P1", source_pdf_path="/x.pdf")
        Question.create(exam=exam, question_number=1, statement="Q", question_type="multiple_choice", options={})
        e2, q2 = WorkspaceService.get_counts(ws2.id)
        assert e2 == 0
        assert q2 == 0
