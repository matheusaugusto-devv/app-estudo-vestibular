import datetime
from pathlib import Path

import pytest
from peewee import IntegrityError

from src.db.connection import database, disconnect
from src.db.models import (
    Exam,
    Question,
    Setting,
    Topic,
    UserAnswer,
    Workspace,
)
from src.db import init_db


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    yield database
    disconnect()
    if database.is_closed() is False:
        database.close()


def test_tables_created(db):
    tables = db.get_tables()
    for t in ("workspaces", "exams", "questions", "user_answers", "topics", "settings"):
        assert t in tables, f"Table {t} not found"


def test_wal_mode_enabled(db):
    mode = db.execute_sql("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"


def test_foreign_keys_enabled(db):
    fk = db.execute_sql("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1


def test_workspace_columns(db):
    w = Workspace.create(name="ENEM 2024", description="Estudo")
    assert w.id is not None
    assert w.name == "ENEM 2024"
    assert w.description == "Estudo"
    assert w.created_at is not None
    assert w.updated_at is not None


def test_exam_columns_and_default_status(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(
        workspace=w,
        title="Prova 1",
        source_pdf_path="/uploads/1/prova.pdf",
    )
    assert exam.status == "pending"
    assert exam.has_answer_key is False
    assert exam.question_count is None
    assert exam.answer_key_pdf_path is None
    assert exam.exam_date is None


def test_question_columns_and_defaults(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(workspace=w, title="P1", source_pdf_path="/x.pdf")
    q = Question.create(
        exam=exam,
        question_number=1,
        statement="Enunciado?",
        question_type="multiple_choice",
        options={"A": "opt", "B": "opt2"},
    )
    assert q.is_answerable is False
    assert q.correct_answer is None
    assert q.topic_primary is None
    assert q.image_paths is None
    assert q.page_number is None


def test_unique_exam_question_number(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(workspace=w, title="P1", source_pdf_path="/x.pdf")
    Question.create(exam=exam, question_number=1, statement="Q1", question_type="multiple_choice", options={})
    with pytest.raises(IntegrityError):
        Question.create(exam=exam, question_number=1, statement="Dup", question_type="multiple_choice", options={})


def test_unique_topic_workspace_name(db):
    w = Workspace.create(name="WS1")
    Topic.create(workspace=w, name="Matemática")
    with pytest.raises(IntegrityError):
        Topic.create(workspace=w, name="Matemática")


def test_unique_setting_key(db):
    Setting.create(key="ai_provider", value="openai")
    with pytest.raises(IntegrityError):
        Setting.create(key="ai_provider", value="gemini")


def test_cascade_delete_workspace(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(workspace=w, title="P1", source_pdf_path="/x.pdf")
    q = Question.create(exam=exam, question_number=1, statement="Q", question_type="multiple_choice", options={})
    UserAnswer.create(question=q, user_answer="A", is_correct=True)
    Topic.create(workspace=w, name="Math")

    w.delete_instance(recursive=True)

    assert Exam.select().where(Exam.id == exam.id).count() == 0
    assert Question.select().where(Question.id == q.id).count() == 0
    assert UserAnswer.select().count() == 0
    assert Topic.select().count() == 0


def test_cascade_delete_exam(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(workspace=w, title="P1", source_pdf_path="/x.pdf")
    q = Question.create(exam=exam, question_number=1, statement="Q", question_type="multiple_choice", options={})
    UserAnswer.create(question=q, user_answer="A", is_correct=False)

    exam.delete_instance(recursive=True)

    assert Question.select().where(Question.id == q.id).count() == 0
    assert UserAnswer.select().count() == 0
    assert Workspace.select().where(Workspace.id == w.id).count() == 1


def test_user_answer_columns(db):
    w = Workspace.create(name="WS1")
    exam = Exam.create(workspace=w, title="P1", source_pdf_path="/x.pdf")
    q = Question.create(exam=exam, question_number=1, statement="Q", question_type="multiple_choice", options={})
    ua = UserAnswer.create(question=q, user_answer="B", is_correct=True)
    assert ua.user_answer == "B"
    assert ua.is_correct is True
    assert ua.answered_at is not None


def test_topic_columns(db):
    w = Workspace.create(name="WS1")
    t = Topic.create(workspace=w, name="Português", question_count=5)
    assert t.question_count == 5
    assert t.name == "Português"


def test_setting_columns(db):
    s = Setting.create(key="onboarding_completed", value="true")
    assert s.value == "true"
    assert s.is_encrypted is False


def test_indexes_exist(db):
    idx_info = db.execute_sql(
        "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
    ).fetchall()
    idx_names = {row[0] for row in idx_info}

    assert any("workspace" in n.lower() and "status" in n.lower() for n in idx_names), \
        "Missing index on exams(workspace_id, status)"
    assert any("exam" in n.lower() and "question" in n.lower() for n in idx_names), \
        "Missing UNIQUE index on questions(exam_id, question_number)"
    assert any("topic_primary" in n.lower() for n in idx_names), \
        "Missing index on questions(topic_primary)"
    assert any("question" in n.lower() and "user_answer" not in n.lower() for n in idx_names), \
        "Missing index on user_answers(question_id)"
    assert any("answered_at" in n.lower() for n in idx_names), \
        "Missing index on user_answers(answered_at)"
    assert any("workspace" in n.lower() and "name" in n.lower() for n in idx_names), \
        "Missing UNIQUE index on topics(workspace_id, name)"
