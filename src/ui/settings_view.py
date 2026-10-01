import logging

import flet as ft

from src.ai.exceptions import AIException
from src.ai.provider_service import AIProviderService
from src.config.credentials import CredentialService
from src.config.settings import ConfigService

logger = logging.getLogger(__name__)

PROVIDERS = [
    ("openai", "OpenAI", ft.Icons.PSYCHOLOGY),
    ("gemini", "Google Gemini", ft.Icons.AUTO_AWESOME),
    ("claude", "Anthropic Claude", ft.Icons.SMART_TOY),
    ("ollama", "Ollama (Local)", ft.Icons.COMPUTER),
]

DEFAULT_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
    "claude": ["claude-3.5-sonnet", "claude-3.5-haiku", "claude-3-opus"],
}


class SettingsView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, spacing=20, margin=20)
        self._page = page
        self._selected_provider = ConfigService.get("ai_provider") or "openai"
        self._connection_tested = False
        self._render()

    def _render(self):
        self.controls.clear()
        self.controls.append(ft.Text("Configurações de IA", size=28, weight=ft.FontWeight.BOLD))

        provider_row = ft.Row(spacing=10)
        for pid, name, icon in PROVIDERS:
            card = ft.Container(
                width=200,
                ink=True,
                border=ft.border.all(2, ft.Colors.PRIMARY if self._selected_provider == pid else ft.Colors.OUTLINE_VARIANT),
                border_radius=10,
                padding=12,
                on_click=lambda e, pid=pid: self._select_provider(pid),
                content=ft.Column([
                    ft.Icon(icon, size=24, color=ft.Colors.PRIMARY),
                    ft.Text(name, size=12, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
            provider_row.controls.append(card)
        self.controls.append(provider_row)

        if self._selected_provider == "ollama":
            current_endpoint = ConfigService.get("ai_endpoint") or "http://localhost:11434"
            self._endpoint_field = ft.TextField(label="URL do Endpoint", value=current_endpoint, width=500)
            self.controls.append(self._endpoint_field)
            self._model_dropdown = ft.Dropdown(label="Modelo", width=500, options=[], value=ConfigService.get("ai_model"))
            self.controls.append(self._model_dropdown)
            self.controls.append(
                ft.Row([
                    ft.OutlinedButton("Carregar Modelos", on_click=lambda _: self._load_ollama_models()),
                    ft.OutlinedButton("Testar Conexão", on_click=lambda _: self._test_connection()),
                ], spacing=10)
            )
        else:
            self._api_key_field = ft.TextField(
                label="API Key", password=True, can_reveal_password=True, width=500,
                value=CredentialService.get_api_key() or "",
            )
            self.controls.append(self._api_key_field)
            models = DEFAULT_MODELS.get(self._selected_provider, [])
            current_model = ConfigService.get("ai_model")
            self._model_dropdown = ft.Dropdown(
                label="Modelo", width=500,
                options=[ft.DropdownOption(key=m, text=m) for m in models],
                value=current_model or (models[0] if models else None),
            )
            self.controls.append(self._model_dropdown)
            self.controls.append(ft.OutlinedButton("Testar Conexão", on_click=lambda _: self._test_connection()))

        self._status_text = ft.Text("", size=12)
        self.controls.append(self._status_text)

        self.controls.append(
            ft.FilledButton("Salvar Configurações", on_click=lambda _: self._save())
        )
        self._page.update()

    def _select_provider(self, pid: str):
        self._selected_provider = pid
        self._connection_tested = False
        self._render()

    def _load_ollama_models(self):
        endpoint = self._endpoint_field.value or "http://localhost:11434"
        try:
            models = AIProviderService.list_models_for("ollama", endpoint=endpoint)
            self._model_dropdown.options = [ft.DropdownOption(key=m, text=m) for m in models]
            if models:
                self._model_dropdown.value = models[0]
            self._status_text.value = f"{len(models)} modelos encontrados."
            self._status_text.color = ft.Colors.GREEN
        except AIException as e:
            self._status_text.value = str(e)
            self._status_text.color = ft.Colors.RED
        self._page.update()

    def _test_connection(self):
        provider = self._selected_provider
        api_key = self._api_key_field.value if provider != "ollama" and hasattr(self, "_api_key_field") else ""
        endpoint = self._endpoint_field.value if provider == "ollama" and hasattr(self, "_endpoint_field") else ""
        model = self._model_dropdown.value or ""

        self._status_text.value = "Testando..."
        self._status_text.color = ft.Colors.ON_SURFACE_VARIANT
        self._page.update()

        try:
            result = AIProviderService.test_provider(provider, api_key=api_key, endpoint=endpoint, model=model)
            if result:
                self._connection_tested = True
                self._status_text.value = "Conexão bem-sucedida!"
                self._status_text.color = ft.Colors.GREEN
            else:
                self._status_text.value = "Falha na conexão."
                self._status_text.color = ft.Colors.RED
        except AIException as e:
            self._connection_tested = False
            msg = str(e)
            if "Credenciais" in msg:
                self._status_text.value = "API Key inválida. Verifique e tente novamente."
            elif "conectar" in msg.lower():
                self._status_text.value = "Não foi possível conectar ao Ollama. Verifique se está rodando."
            else:
                self._status_text.value = msg
            self._status_text.color = ft.Colors.RED
        except Exception as e:
            self._connection_tested = False
            self._status_text.value = f"Erro: {e}"
            self._status_text.color = ft.Colors.RED
        self._page.update()

    def _save(self):
        ConfigService.set("ai_provider", self._selected_provider)
        ConfigService.set("ai_model", self._model_dropdown.value or "")
        if self._selected_provider == "ollama":
            ConfigService.set("ai_endpoint", self._endpoint_field.value or "")
        else:
            CredentialService.save_api_key(self._api_key_field.value or "")
        self._status_text.value = "Configurações salvas!"
        self._status_text.color = ft.Colors.GREEN
        self._page.update()
