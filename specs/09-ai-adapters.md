# Spec 09 — AI Adapters (Abstração Multi-Provedor)

## Objetivo

Definir a camada de abstração unificada para integração com múltiplos provedores de IA (OpenAI, Google Gemini, Anthropic Claude, Ollama), garantindo uma interface consistente para o pipeline de extração e o parser de gabarito.

## Contexto

A aplicação suporta 4 provedores de IA com APIs diferentes. Para evitar acoplamento e permitir troca de provedor sem refactor do pipeline, é necessário uma camada de adapters com interface comum. Cada adapter traduz as chamadas da interface unificada para a API específica do provedor.

## Arquitetura

```
┌─────────────────────────────────────────┐
│           AIProviderService              │
│  (Factory: retorna adapter baseado em    │
│   settings.ai_provider)                  │
├─────────────────────────────────────────┤
│         Interface: IAIAdapter            │
│  - test_connection() → bool              │
│  - extract(prompt, schema) → dict        │
│  - list_models() → list[str]             │
├──────┬──────────┬──────────┬─────────────┤
│OpenAI│ Gemini   │ Claude   │   Ollama    │
│Adapter│ Adapter  │ Adapter  │   Adapter   │
└──────┴──────────┴──────────┴─────────────┘
```

## Interface Unificada (IAIAdapter)

```python
class IAIAdapter(ABC):
    @abstractmethod
    def test_connection(self) -> bool:
        """Valida se a configuração (API key / endpoint) está correta."""
        pass

    @abstractmethod
    def extract(self, system_prompt: str, user_prompt: str, response_schema: dict) -> dict:
        """
        Envia prompt ao LLM e retorna JSON estruturado validado contra response_schema.
        Levanta exceção em caso de falha ou timeout.
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """Retorna lista de modelos disponíveis para o provedor."""
        pass
```

## Adapters

### OpenAIAdapter

- **SDK:** `openai` (Python SDK oficial)
- **Endpoint:** `https://api.openai.com/v1`
- **Auth:** Bearer token (API Key)
- **Modelos:** gpt-4o, gpt-4o-mini, gpt-4-turbo
- **Structured Output:** Usar `response_format` com JSON Schema (OpenAI Structured Outputs)
- **list_models:** GET `/v1/models`
- **test_connection:** GET `/v1/models` com a API Key — 200 = OK

### GeminiAdapter

- **SDK:** `google-generativeai` (Python SDK oficial)
- **Endpoint:** Google AI API
- **Auth:** API Key (query param `?key=`)
- **Modelos:** gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash
- **Structured Output:** Usar `generation_config` com `response_mime_type="application/json"` e `response_schema`
- **list_models:** `genai.list_models()`
- **test_connection:** Tentar listar modelos — sucesso = OK

### ClaudeAdapter

- **SDK:** `anthropic` (Python SDK oficial)
- **Endpoint:** `https://api.anthropic.com/v1`
- **Auth:** `x-api-key` header
- **Modelos:** claude-3.5-sonnet, claude-3.5-haiku, claude-3-opus
- **Structured Output:** Claude não suporta JSON Schema nativo — usar prompt instruction + parsing manual do JSON retornado
- **list_models:** Lista hardcoded (Claude não tem endpoint de listagem)
- **test_connection:** Mensagem simples (messages API) — 200 = OK

### OllamaAdapter

- **SDK:** `requests` (HTTP direto) ou `ollama` (Python SDK)
- **Endpoint:** Configurável (default: `http://localhost:11434`)
- **Auth:** Nenhuma (local)
- **Modelos:** Dinâmicos via GET `/api/tags`
- **Structured Output:** Usar `format` parameter com JSON Schema (Ollama suporta structured outputs)
- **list_models:** GET `/api/tags` → parsear `models[].name`
- **test_connection:** GET `/api/tags` — 200 = OK

## AIProviderService (Factory)

```python
class AIProviderService:
    @staticmethod
    def get_adapter() -> IAIAdapter:
        provider = Settings.get("ai_provider")
        model = Settings.get("ai_model")
        api_key = Keyring.get("ai_api_key") or Settings.get("ai_api_key")
        endpoint = Settings.get("ai_endpoint")

        if provider == "openai":
            return OpenAIAdapter(api_key=api_key, model=model)
        elif provider == "gemini":
            return GeminiAdapter(api_key=api_key, model=model)
        elif provider == "claude":
            return ClaudeAdapter(api_key=api_key, model=model)
        elif provider == "ollama":
            return OllamaAdapter(endpoint=endpoint, model=model)
        else:
            raise ValueError(f"Provedor não suportado: {provider}")
```

## Regras de Negócio

1. Apenas um provedor está ativo por vez (definido em `settings.ai_provider`).
2. O adapter é instanciado sob demanda (não singleton — cria novo a cada chamada de pipeline).
3. Todas as chamadas ao LLM têm timeout configurável (default: 60s).
4. Em caso de rate limit (HTTP 429), aplicar backoff exponencial: 1s, 2s, 4s (máx 3 tentativas).
5. Erros de autenticação (HTTP 401/403) são tratados especificamente com mensagem clara.
6. O método `extract()` deve sempre retornar um `dict` válido — se o LLM retornar JSON inválido, tentar repair/parse, e se falhar, levantar exceção.
7. Para Claude (sem JSON Schema nativo), o adapter deve incluir a instrução de formato no prompt e fazer parse do JSON retornado.
8. A lista de modelos pode ser atualizada (cacheada por sessão para evitar chamadas repetidas).

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-AI-01 | Implementar interface `IAIAdapter` com 3 métodos abstratos                  |
| FR-AI-02 | Implementar `OpenAIAdapter` com SDK oficial                                 |
| FR-AI-03 | Implementar `GeminiAdapter` com SDK oficial                                 |
| FR-AI-04 | Implementar `ClaudeAdapter` com SDK oficial                                 |
| FR-AI-05 | Implementar `OllamaAdapter` com requests HTTP                               |
| FR-AI-06 | Implementar `AIProviderService` como factory                                |
| FR-AI-07 | `test_connection()` valida credenciais/endpoint para cada provedor          |
| FR-AI-08 | `extract()` envia prompt e retorna dict validado contra schema              |
| FR-AI-09 | `list_models()` retorna modelos disponíveis                                 |
| FR-AI-10 | Backoff exponencial em caso de rate limit (429)                             |
| FR-AI-11 | Tratamento específico de erro de autenticação (401/403)                     |
| FR-AI-12 | Timeout configurável (default 60s)                                          |
| FR-AI-13 | Para Claude, incluir schema no prompt e fazer parse manual do JSON         |
| FR-AI-14 | Para Ollama, usar `format` parameter para structured output                |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-AI-01 | Adapters devem ser independentes (sem acoplamento entre eles)          |
| NFR-AI-02 | Novo provedor pode ser adicionado implementando apenas `IAIAdapter`    |
| NFR-AI-03 | Não usar `litellm` ou wrapper externo — adapters próprios em Python   |

## Casos de Erro

| ID    | Cenário                                           | Comportamento                                            |
|-------|---------------------------------------------------|----------------------------------------------------------|
| ERR-AI-01 | API Key inválida (401/403)                     | Exceção `AIAuthError`: "Credenciais inválidas para {provider}." |
| ERR-AI-02 | Rate limit (429)                               | Backoff exponencial (1s, 2s, 4s); se persistir, `AIRateLimitError` |
| ERR-AI-03 | Timeout (60s)                                 | Exceção `AITimeoutError`: "Tempo limite excedido."       |
| ERR-AI-04 | LLM retorna JSON inválido                     | Tentar repair/parse; se falhar, `AIResponseError`        |
| ERR-AI-05 | Endpoint Ollama inacessível (ConnectionError) | Exceção `AIConnectionError`: "Não foi possível conectar." |
| ERR-AI-06 | Provedor não configurado                       | Exceção `AINotConfiguredError`: "Configure a IA nas Configurações." |
| ERR-AI-07 | Modelo não existe mais no provedor             | Exceção `AIModelError`: "Modelo não disponível."         |

## Hierarquia de Exceções

```
AIException (base)
├── AIAuthError          → credenciais inválidas
├── AIRateLimitError     → rate limit excedido
├── AITimeoutError       → timeout
├── AIResponseError      → resposta inválida do LLM
├── AIConnectionError    → conexão falhou (Ollama)
├── AINotConfiguredError → IA não configurada
└── AIModelError         → modelo não disponível
```

## Critérios de Aceitação

1. A interface `IAIAdapter` define `test_connection()`, `extract()`, `list_models()`.
2. `OpenAIAdapter` implementa a interface usando o SDK oficial.
3. `GeminiAdapter` implementa a interface usando o SDK oficial.
4. `ClaudeAdapter` implementa a interface usando o SDK oficial.
5. `OllamaAdapter` implementa a interface usando requests HTTP.
6. `AIProviderService.get_adapter()` retorna o adapter correto baseado em `settings.ai_provider`.
7. `test_connection()` valida credenciais/endpoint para cada provedor.
8. `extract()` envia prompt e retorna dict validado.
9. `list_models()` retorna modelos disponíveis (dinâmico para Ollama).
10. Backoff exponencial é aplicado em caso de rate limit.
11. Erros de autenticação têm mensagem específica.
12. Timeout é respeitado (60s default).
13. Claude usa prompt instruction + parse manual para JSON.
14. Ollama usa `format` parameter para structured output.
15. Exceções seguem a hierarquia definida.

## Fora de Escopo

- Uso de `litellm` como wrapper unificado — adapters próprios.
- Streaming de respostas (resposta completa em uma chamada).
- Cache de respostas do LLM (futuro).
- Suporte a mais de 4 provedores (outros podem ser adicionados depois).
- Envio de imagens ao LLM multimodal (visão) — futura melhoria.
