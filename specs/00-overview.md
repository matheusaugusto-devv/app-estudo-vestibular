# Spec 00 — Visão Geral e Arquitetura

## Objetivo

Aplicação desktop local para estudantes, concurseiros e vestibulandos organizarem e praticarem questões de provas em PDF. O sistema ingere PDFs de provas (e gabaritos opcionais), extrai questões estruturadas via pipeline híbrido (OCR + LLM), e oferece módulos de prática/simulado com feedback imediato e analytics por tópicos.

## Contexto

O usuário típico baixa PDFs de provas anteriores (concursos, ENEM, vestibulares, residência médica) e precisa de uma ferramenta que automatize a extração de questões, organize o estudo por tópicos e permita praticar com simulados. A aplicação roda 100% local, sem servidor backend próprio — a única dependência externa é a API do provedor de IA escolhido pelo usuário.

## Tech Stack

| Camada            | Tecnologia                                                        |
|-------------------|-------------------------------------------------------------------|
| Linguagem         | Python 3.11+                                                      |
| UI                | Flet (Flutter para Python)                                        |
| Banco de Dados    | SQLite com WAL mode habilitado, ORM Peewee                        |
| Processamento PDF | PyMuPDF (fitz) + pdfplumber + Pillow/OpenCV                      |
| Integração IA     | Multi-provedor (OpenAI, Gemini, Claude, Ollama) via adapters      |

## Arquitetura de Camadas

```
┌─────────────────────────────────────────────┐
│                  UI Layer (Flet)              │
│   Views: Onboarding, Workspaces, Upload,     │
│   Questões, Tópicos, Configurações           │
├─────────────────────────────────────────────┤
│              Application Layer               │
│   Services: ExamService, QuestionService,    │
│   WorkspaceService, AnswerKeyService,        │
│   TopicService, AIProviderService            │
├─────────────────────────────────────────────┤
│           Pipeline Layer (Ingestão)          │
│   PDFParser → ImageExtractor → LLMExtractor  │
│   → AnswerKeyParser                          │
├─────────────────────────────────────────────┤
│            Infrastructure Layer              │
│   Database (Peewee/SQLite), FileStorage,     │
│   AI Adapters (OpenAI, Gemini, Claude,       │
│   Ollama), AssetManager                      │
└─────────────────────────────────────────────┘
```

## Estrutura de Diretórios do Projeto

```
/src
  /ui          → Views e componentes Flet
  /services    → Lógica de aplicação (use cases)
  /pipeline    → Pipeline de extração (PDF, imagem, LLM)
  /db          → Modelos Peewee, migrações, conexão
  /ai          → Adapters de provedores de IA
  /storage     → Gerenciamento de arquivos locais e assets
  /config      → Configurações da aplicação
  main.py      → Entry point
/data
  /assets      → Imagens recortadas ({workspace_id}/{question_id}.png)
  /uploads     → PDFs enviados pelo usuário
  app.db       → Banco SQLite
/tests
/specs
```

## Regras de Negócio Globais

1. A aplicação é totalmente local — nenhum dado do usuário sai do dispositivo exceto chamadas à API de IA (controladas pelo usuário).
2. Cada Workspace é isolado: provas, questões e assets de um workspace não são visíveis em outro.
3. Questões de provas sem gabarito processado ficam **bloqueadas** no módulo de simulado/prática.
4. As credenciais de IA são armazenadas de forma segura via `keyring` do SO ou tabela `settings` com cifragem.
5. O WAL mode do SQLite deve ser habilitado na inicialização para suportar concorrência de leitura durante escrita.

## Requisitos Não Funcionais

| ID     | Requisito                                                                 | Métrica / Critério                                  |
|--------|---------------------------------------------------------------------------|-----------------------------------------------------|
| NFR-01 | Tempo de inicialização da aplicação                                      | < 3 segundos                                        |
| NFR-02 | Tempo de extração de uma prova de 50 questões (incluindo LLM)            | < 5 minutos                                         |
| NFR-03 | Suporte a provas de até 200 questões                                      | Sem travamento ou OOM                               |
| NFR-04 | Armazenamento de assets organizado por workspace                          | `/data/assets/{workspace_id}/{question_id}.png`    |
| NFR-05 | Backup exportável do banco de dados                                      | Export para arquivo `.db` ou `.json`               |
| NFR-06 | Banco SQLite em WAL mode                                                  | `PRAGMA journal_mode=WAL` ao conectar               |
| NFR-07 | Compatibilidade                                                           | Windows 10+, macOS 12+, Linux (Ubuntu 22.04+)       |
| NFR-08 | Resolução mínima                                                          | 1280x720                                            |

## Fora de Escopo

- Sincronização na nuvem (Google Drive, Dropbox, etc.)
- Aplicação mobile ou web
- Compartilhamento de questões entre usuários
- Geração automática de questões por IA (apenas extração de PDFs existentes)
- Login/autenticação de usuário (app é single-user, local)
- Impressão/exportação de provas em PDF
