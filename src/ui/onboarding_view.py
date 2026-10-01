import logging

import flet as ft

from src.ai.exceptions import AIException
from src.ai.provider_service import AIProviderService
from src.config.credentials import CredentialService
from src.config.settings import ConfigService

logger = logging.getLogger(__name__)

PROVIDERS = [
    ("openai", "OpenAI", "gpt-4o, gpt-4o-mini", ft.Icons.PSYCHOLOGY),
    ("gemini", "Google Gemini", "gemini-1.5-pro, gemini-1.5-flash", ft.Icons.AUTO_AWESOME),
    ("claude", "Anthropic Claude", "claude-3.5-sonnet, claude-3-haiku", ft.Icons.SMART_TOY),
    ("ollama", "Ollama (Local)", "Modelos locais disponíveis", ft.Icons.COMPUTER),
]

DEFAULT_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "gemini": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"],
    "claude": ["claude-3.5-sonnet", "claude-3.5-haiku", "claude-3-opus"],
}


class OnboardingView(ft.Column):
    def __init__(self, page: ft.Page, on_complete=None):
        super().__init__(expand=True, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self._page = page
        self._on_complete = on_complete
        self._step = 0
        self._selected_provider = None
        self._connection_tested = False
        self._api_key = ""
        self._endpoint = "http://localhost:11434"
        self._model = ""

        self._content = ft.Container(
            width=600,
            padding=40,
            bgcolor=ft.Colors.SURFACE,
            border_radius=12,
            content=ft.Column([], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
        self._progress = ft.ProgressBar(width=400, value=0.2)
        self.controls = [self._progress, self._content]
        self._render()

    def _render(self):
        self._progress.value = (self._step + 1) / 5
        steps = [
            self._step_welcome,
            self._step_how_it_works,
            self._step_choose_provider,
            self._step_credentials,
            self._step_confirmation,
        ]
        self._content.content.controls = steps[self._step]()
        self._page.update()

    def _step_welcome(self):
        return [
            ft.Icon(ft.Icons.SCHOOL, size=64, color=ft.Colors.PRIMARY),
            ft.Text("EstudoVest", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("Organize e pratique questões de provas em PDF com ajuda de IA.", size=14, color=ft.Colors.ON_SURFACE_VARIANT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.FilledButton("Começar", on_click=lambda _: self._next()),
        ]

    def _step_how_it_works(self):
        cards_data = [
            (ft.Icons.WORK, "Crie um Workspace", "Organize suas provas por concurso/exame."),
            (ft.Icons.UPLOAD_FILE, "Faça upload de PDFs", "Envie provas e gabaritos."),
            (ft.Icons.AUTO_FIX_HIGH, "Extração automática", "A IA extrai questões, alternativas, imagens e tópicos."),
            (ft.Icons.QUIZ, "Pratique", "Responda questões, receba feedback e acompanhe seu desempenho."),
        ]
        cards = []
        for icon, title, desc in cards_data:
            cards.append(
                ft.Card(
                    content=ft.Container(
                        padding=16,
                        content=ft.Column([
                            ft.Icon(icon, size=32, color=ft.Colors.PRIMARY),
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(desc, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ),
                    expand=True,
                )
            )
        return [
            ft.Text("Como funciona", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(cards, spacing=10),
            ft.Container(height=20),
            ft.Row([
                ft.TextButton("Voltar", on_click=lambda _: self._prev()),
                ft.FilledButton("Próximo", on_click=lambda _: self._next()),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=400),
        ]

    def _step_choose_provider(self):
        cards = []
        for pid, name, models_desc, icon in PROVIDERS:
            cards.append(
                ft.Container(
                    width=260,
                    ink=True,
                    border=ft.border.all(2, ft.Colors.PRIMARY if self._selected_provider == pid else ft.Colors.OUTLINE_VARIANT),
                    border_radius=10,
                    padding=16,
                    on_click=lambda e, pid=pid: self._select_provider(pid),
                    content=ft.Column([
                        ft.Icon(icon, size=32, color=ft.Colors.PRIMARY),
                        ft.Text(name, size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(models_desc, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            )
        return [
            ft.Text("Escolha o Provedor de IA", size=24, weight=ft.FontWeight.BOLD),
            ft.Row(cards[:2], spacing=10),
            ft.Row(cards[2:], spacing=10),
            ft.Container(height=20),
            ft.Row([
                ft.TextButton("Voltar", on_click=lambda _: self._prev()),
                ft.FilledButton("Próximo", on_click=lambda _: self._next(), disabled=self._selected_provider is None),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=400),
        ]

    def _select_provider(self, pid: str):
        self._selected_provider = pid
        self._connection_tested = False
        self._render()

    def _step_credentials(self):
        provider = self._selected_provider
        if provider is None:
            return [ft.Text("Selecione um provedor primeiro.")]

        provider_name = dict((p[0], p[1]) for p in PROVIDERS).get(provider, provider)
        fields = [ft.Text(f"Configuração — {provider_name}", size=24, weight=ft.FontWeight.BOLD)]

        if provider == "ollama":
            self._endpoint_field = ft.TextField(
                label="URL do Endpoint",
                value=self._endpoint,
                width=400,
                autofocus=True,
            )
            fields.extend([
                self._endpoint_field,
                ft.Container(
                    content=ft.Row([
                        ft.ProgressRing(width=16, height=16, visible=False),
                        ft.Text("", size=12),
                    ]),
                    width=400,
                ),
            ])
            self._model_dropdown = ft.Dropdown(
                label="Modelo",
                width=400,
                options=[],
            )
            fields.append(self._model_dropdown)
            fields.append(
                ft.Row([
                    ft.OutlinedButton("Carregar Modelos", on_click=lambda _: self._load_ollama_models()),
                    ft.OutlinedButton("Testar Conexão", on_click=lambda _: self._test_connection()),
                ], spacing=10)
            )
        else:
            self._api_key_field = ft.TextField(
                label="API Key",
                password=True,
                can_reveal_password=True,
                width=400,
                value=self._api_key,
                autofocus=True,
            )
            fields.append(self._api_key_field)
            models = DEFAULT_MODELS.get(provider, [])
            self._model_dropdown = ft.Dropdown(
                label="Modelo",
                width=400,
                options=[ft.DropdownOption(key=m, text=m) for m in models],
                value=models[0] if models else None,
            )
            fields.append(self._model_dropdown)
            fields.append(
                ft.OutlinedButton("Testar Conexão", on_click=lambda _: self._test_connection())
            )

        self._status_text = ft.Text("", size=12)
        fields.append(self._status_text)

        fields.append(
            ft.Row([
                ft.TextButton("Voltar", on_click=lambda _: self._prev()),
                ft.FilledButton("Próximo", on_click=lambda _: self._next(), disabled=not self._connection_tested),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=400)
        )
        return fields

    def _load_ollama_models(self):
        endpoint = self._endpoint_field.value or "http://localhost:11434"
        self._endpoint = endpoint
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

        self._api_key = api_key
        self._endpoint = endpoint
        self._model = model

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
                self._connection_tested = False
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

        self._render()

    def _step_confirmation(self):
        provider_name = dict((p[0], p[1]) for p in PROVIDERS).get(self._selected_provider, self._selected_provider)
        model = self._model or "—"
        endpoint_or_key = self._endpoint if self._selected_provider == "ollama" else "••••••••"
        label = "Endpoint" if self._selected_provider == "ollama" else "API Key"

        return [
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=48, color=ft.Colors.GREEN),
            ft.Text("Confirmação", size=24, weight=ft.FontWeight.BOLD),
            ft.Column([
                ft.Text(f"Provedor: {provider_name}", size=14),
                ft.Text(f"Modelo: {model}", size=14),
                ft.Text(f"{label}: {endpoint_or_key}", size=14),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([
                ft.TextButton("Voltar", on_click=lambda _: self._prev()),
                ft.FilledButton("Finalizar", on_click=lambda _: self._finish()),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=400),
        ]

    def _next(self):
        if self._step < 4:
            self._step += 1
            self._render()

    def _prev(self):
        if self._step > 0:
            self._step -= 1
            self._render()

    def _finish(self):
        ConfigService.set("ai_provider", self._selected_provider)
        ConfigService.set("ai_model", self._model)
        if self._selected_provider == "ollama":
            ConfigService.set("ai_endpoint", self._endpoint)
        else:
            CredentialService.save_api_key(self._api_key)
        ConfigService.mark_onboarding_completed()
        if self._on_complete:
            self._on_complete()
