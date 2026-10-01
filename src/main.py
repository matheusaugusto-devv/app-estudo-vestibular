import flet as ft
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ASSETS_DIR = DATA_DIR / "assets"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "app.db"


def _ensure_dirs():
    for d in (DATA_DIR, ASSETS_DIR, UPLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)


class AppShell(ft.Column):
    NAV_LABELS = ["Workspaces", "Provas", "Questões", "Tópicos", "Configurações"]

    def __init__(self, page: ft.Page):
        super().__init__(expand=True, spacing=0)
        self._page = page
        self.rail = ft.NavigationRail(
            selected_index=0,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.WORK_OUTLINE, selected_icon=ft.Icons.WORK, label="Workspaces"),
                ft.NavigationRailDestination(icon=ft.Icons.DESCRIPTION_OUTLINED, selected_icon=ft.Icons.DESCRIPTION, label="Provas"),
                ft.NavigationRailDestination(icon=ft.Icons.QUIZ_OUTLINED, selected_icon=ft.Icons.QUIZ, label="Questões"),
                ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS_OUTLINED, selected_icon=ft.Icons.ANALYTICS, label="Tópicos"),
                ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Configurações"),
            ],
            on_change=self._on_nav_change,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
        )
        self.content_area = ft.Container(expand=True, padding=20)
        self._update_content()
        self.controls = [
            ft.Row(
                controls=[
                    self.rail,
                    ft.VerticalDivider(width=1),
                    self.content_area,
                ],
                expand=True,
            )
        ]

    def _on_nav_change(self, _e):
        self._update_content()
        self._page.update()

    def _update_content(self):
        idx = self.rail.selected_index or 0
        name = self.NAV_LABELS[idx]
        if name == "Configurações":
            from src.ui.settings_view import SettingsView
            self.content_area.content = SettingsView(self._page)
        elif name == "Workspaces":
            from src.ui.workspace_list_view import WorkspaceListView
            self.content_area.content = WorkspaceListView(self._page)
        else:
            self.content_area.content = ft.Column(
                controls=[
                    ft.Text(name, size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"Módulo {name} — aguardando implementação da spec correspondente.",
                        size=14,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ]
            )


def main(page: ft.Page):
    _ensure_dirs()
    from src.db import init_db
    init_db(DB_PATH)

    page.title = "EstudoVest"
    page.theme_mode = ft.ThemeMode.SYSTEM

    from src.config.settings import ConfigService
    if not ConfigService.is_onboarding_completed():
        from src.ui.onboarding_view import OnboardingView
        def _on_complete():
            page.clean()
            page.add(AppShell(page))
            page.update()
        page.add(OnboardingView(page, on_complete=_on_complete))
    else:
        page.add(AppShell(page))


if __name__ == "__main__":
    ft.run(target=main)
