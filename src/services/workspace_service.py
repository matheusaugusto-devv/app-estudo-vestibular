import datetime
import logging
import shutil
from pathlib import Path

from src.config.settings import ConfigService
from src.db.models import Exam, Question, Workspace

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
ASSETS_DIR = DATA_DIR / "assets"


class WorkspaceService:
    @staticmethod
    def list_all():
        return list(Workspace.select().order_by(Workspace.created_at.desc()))

    @staticmethod
    def get(workspace_id: int) -> Workspace:
        return Workspace.get_by_id(workspace_id)

    @staticmethod
    def get_active() -> Workspace | None:
        wid = ConfigService.get("default_workspace_id")
        if wid is not None:
            try:
                return Workspace.get_by_id(int(wid))
            except Workspace.DoesNotExist:
                pass
        ws = Workspace.select().first()
        if ws:
            ConfigService.set("default_workspace_id", str(ws.id))
        return ws

    @staticmethod
    def set_active(workspace_id: int) -> None:
        ConfigService.set("default_workspace_id", str(workspace_id))

    @staticmethod
    def get_counts(workspace_id: int) -> tuple[int, int]:
        exam_count = Exam.select().where(Exam.workspace == workspace_id).count()
        question_count = (
            Question
            .select()
            .join(Exam)
            .where(Exam.workspace == workspace_id)
            .count()
        )
        return exam_count, question_count

    @staticmethod
    def create(name: str, description: str | None = None) -> Workspace:
        name = name.strip()
        if not name:
            raise ValueError("O nome do workspace é obrigatório.")
        if len(name) > 100:
            raise ValueError("O nome do workspace deve ter no máximo 100 caracteres.")
        if Workspace.select().where(Workspace.name == name).exists():
            raise ValueError("Já existe um workspace com este nome.")
        if description and len(description) > 500:
            raise ValueError("A descrição deve ter no máximo 500 caracteres.")
        ws = Workspace.create(name=name, description=description)
        assets_path = ASSETS_DIR / str(ws.id)
        try:
            assets_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Falha ao criar pasta de assets para workspace %s: %s", ws.id, e)
        return ws

    @staticmethod
    def update(workspace_id: int, name: str, description: str | None = None) -> Workspace:
        name = name.strip()
        if not name:
            raise ValueError("O nome do workspace é obrigatório.")
        if len(name) > 100:
            raise ValueError("O nome do workspace deve ter no máximo 100 caracteres.")
        existing = Workspace.select().where(
            (Workspace.name == name) & (Workspace.id != workspace_id)
        ).first()
        if existing:
            raise ValueError("Já existe um workspace com este nome.")
        if description and len(description) > 500:
            raise ValueError("A descrição deve ter no máximo 500 caracteres.")
        ws = Workspace.get_by_id(workspace_id)
        ws.name = name
        ws.description = description
        ws.updated_at = datetime.datetime.now()
        ws.save()
        return ws

    @staticmethod
    def delete(workspace_id: int) -> None:
        total = Workspace.select().count()
        if total <= 1:
            raise ValueError("Não é possível deletar o único workspace.")
        ws = Workspace.get_by_id(workspace_id)
        ws.delete_instance(recursive=True)
        assets_path = ASSETS_DIR / str(workspace_id)
        if assets_path.exists():
            try:
                shutil.rmtree(assets_path)
            except Exception as e:
                logger.warning("Falha ao remover pasta de assets do workspace %s: %s", workspace_id, e)
        active_id = ConfigService.get("default_workspace_id")
        if active_id and int(active_id) == workspace_id:
            remaining = Workspace.select().first()
            if remaining:
                ConfigService.set("default_workspace_id", str(remaining.id))
