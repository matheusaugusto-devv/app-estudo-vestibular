import flet as ft

from src.services.workspace_service import WorkspaceService


class WorkspaceListView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, spacing=20, margin=20)
        self._page = page
        self._render()

    def _render(self):
        self.controls.clear()
        self.controls.append(
            ft.Row([
                ft.Text("Workspaces", size=28, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.FloatingActionButton(
                    icon=ft.Icons.ADD,
                    content=ft.Text("Novo Workspace"),
                    on_click=lambda _: self._open_create_dialog(),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        workspaces = WorkspaceService.list_all()
        active = WorkspaceService.get_active()
        active_id = active.id if active else None

        if not workspaces:
            self.controls.append(
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column([
                        ft.Icon(ft.Icons.WORK_OFF, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text("Nenhum workspace. Crie o primeiro!", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            )
            self._page.update()
            return

        cards_row = ft.Row(spacing=15, wrap=True)
        for ws in workspaces:
            exam_count, question_count = WorkspaceService.get_counts(ws.id)
            is_active = ws.id == active_id
            card = ft.Card(
                width=280,
                content=ft.Container(
                    padding=16,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.WORK, color=ft.Colors.PRIMARY if is_active else ft.Colors.ON_SURFACE_VARIANT, size=28),
                            ft.Text(ws.name, size=16, weight=ft.FontWeight.BOLD, expand=True),
                        ]),
                        ft.Text(
                            ws.description or "Sem descrição",
                            size=12, color=ft.Colors.ON_SURFACE_VARIANT, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Container(height=8),
                        ft.Row([
                            ft.Icon(ft.Icons.DESCRIPTION, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(f"{exam_count} prova{'s' if exam_count != 1 else ''}", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Container(width=12),
                            ft.Icon(ft.Icons.QUIZ, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(f"{question_count} questão{'es' if question_count != 1 else ''}", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        ]),
                        ft.Container(height=12),
                        ft.Row([
                            ft.FilledTonalButton(
                                "Abrir" if not is_active else "Ativo",
                                icon=ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.OPEN_IN_NEW,
                                on_click=lambda e, wid=ws.id: self._select_workspace(wid),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT, icon_color=ft.Colors.ON_SURFACE_VARIANT,
                                tooltip="Editar", on_click=lambda e, wid=ws.id: self._open_edit_dialog(wid),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                tooltip="Deletar", on_click=lambda e, wid=ws.id: self._open_delete_dialog(wid),
                            ),
                        ], spacing=4),
                    ]),
                ),
            )
            cards_row.controls.append(card)

        self.controls.append(cards_row)
        self._page.update()

    def _select_workspace(self, workspace_id: int):
        WorkspaceService.set_active(workspace_id)
        self._page.open(ft.SnackBar(content=ft.Text("Workspace ativo alterado."), bgcolor=ft.Colors.GREEN_700))
        self._render()

    def _open_create_dialog(self):
        self._open_form_dialog(None)

    def _open_edit_dialog(self, workspace_id: int):
        self._open_form_dialog(workspace_id)

    def _open_form_dialog(self, workspace_id: int | None):
        ws = None
        if workspace_id is not None:
            ws = WorkspaceService.get(workspace_id)

        name_field = ft.TextField(
            label="Nome", value=ws.name if ws else "", max_length=100,
            autofocus=True, width=400,
        )
        desc_field = ft.TextField(
            label="Descrição (opcional)", value=ws.description if ws else "",
            max_length=500, multiline=True, min_lines=2, max_lines=4, width=400,
        )
        error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

        def _save(_e):
            name = name_field.value or ""
            desc = desc_field.value or ""
            try:
                if workspace_id is not None:
                    WorkspaceService.update(workspace_id, name, desc or None)
                else:
                    WorkspaceService.create(name, desc or None)
                self._page.pop_dialog()
                self._render()
            except ValueError as ex:
                error_text.value = str(ex)
                error_text.visible = True
                self._page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Workspace" if workspace_id else "Novo Workspace"),
            content=ft.Column([
                name_field,
                desc_field,
                error_text,
            ], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._page.pop_dialog()),
                ft.FilledButton("Salvar", on_click=_save),
            ],
        )
        self._page.show_dialog(dialog)

    def _open_delete_dialog(self, workspace_id: int):
        ws = WorkspaceService.get(workspace_id)

        def _delete(_e):
            try:
                WorkspaceService.delete(workspace_id)
                self._page.pop_dialog()
                self._render()
            except ValueError as ex:
                self._page.pop_dialog()
                self._page.open(ft.SnackBar(content=ft.Text(str(ex)), bgcolor=ft.Colors.RED_700))
                self._render()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Deletar Workspace"),
            content=ft.Text(
                f"Tem certeza que deseja deletar o workspace '{ws.name}'? "
                "Todas as provas, questões e registros serão removidos permanentemente."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._page.pop_dialog()),
                ft.FilledButton("Deletar", bgcolor=ft.Colors.RED_700, on_click=_delete),
            ],
        )
        self._page.show_dialog(dialog)
