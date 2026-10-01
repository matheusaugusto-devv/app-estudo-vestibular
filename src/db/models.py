from peewee import (
    AutoField,
    BooleanField,
    DateField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    JSONField,
    Model,
    SqliteDatabase,
    TextField,
)

from src.db.connection import database


class BaseModel(Model):
    class Meta:
        database = database


class Workspace(BaseModel):
    id = AutoField()
    name = TextField(null=False)
    description = TextField(null=True)
    created_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())
    updated_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "workspaces"


class Exam(BaseModel):
    id = AutoField()
    workspace = ForeignKeyField(Workspace, backref="exams", on_delete="CASCADE", null=False)
    title = TextField(null=False)
    exam_date = DateField(null=True)
    source_pdf_path = TextField(null=False)
    answer_key_pdf_path = TextField(null=True)
    has_answer_key = BooleanField(null=False, default=False)
    status = TextField(null=False, default="pending")
    question_count = IntegerField(null=True)
    created_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())
    updated_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "exams"
        indexes = (
            (("workspace", "status"), False),
        )


class Question(BaseModel):
    id = AutoField()
    exam = ForeignKeyField(Exam, backref="questions", on_delete="CASCADE", null=False)
    question_number = IntegerField(null=False)
    statement = TextField(null=False)
    question_type = TextField(null=False)
    options = JSONField(null=False)
    correct_answer = TextField(null=True)
    topic_primary = TextField(null=True)
    topic_secondary = TextField(null=True)
    image_paths = JSONField(null=True)
    page_number = IntegerField(null=True)
    is_answerable = BooleanField(null=False, default=False)
    created_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "questions"
        indexes = (
            (("exam", "question_number"), True),
            (("exam",), False),
            (("topic_primary",), False),
        )


class UserAnswer(BaseModel):
    id = AutoField()
    question = ForeignKeyField(Question, backref="user_answers", on_delete="CASCADE", null=False)
    user_answer = TextField(null=False)
    is_correct = BooleanField(null=False)
    answered_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "user_answers"
        indexes = (
            (("question",), False),
            (("answered_at",), False),
        )


class Topic(BaseModel):
    id = AutoField()
    workspace = ForeignKeyField(Workspace, backref="topics", on_delete="CASCADE", null=False)
    name = TextField(null=False)
    question_count = IntegerField(null=False, default=0)
    created_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "topics"
        indexes = (
            (("workspace", "name"), True),
            (("workspace",), False),
        )


class Setting(BaseModel):
    id = AutoField()
    key = TextField(null=False, unique=True)
    value = TextField(null=True)
    is_encrypted = BooleanField(null=False, default=False)
    updated_at = DateTimeField(null=False, default=lambda: __import__("datetime").datetime.now())

    class Meta:
        database = database
        table_name = "settings"


ALL_MODELS = [Workspace, Exam, Question, UserAnswer, Topic, Setting]
