# Tasks — Breakdown de Implementação

Este arquivo organiza a implementação em fases sequenciais. Cada fase contém tarefas granulares mapeadas às specs.

---

## Fase 0 — Setup do Projeto

- [ ] T0.1 — Criar estrutura de diretórios (`/src/{ui,services,pipeline,db,ai,storage,config}`, `/data`, `/tests`)
- [ ] T0.2 — Criar `requirements.txt` com dependências: `flet`, `peewee`, `PyMuPDF`, `pdfplumber`, `Pillow`, `opencv-python`, `openai`, `google-generativeai`, `anthropic`, `keyring`, `requests`
- [ ] T0.3 — Criar `src/main.py` (entry point Flet)
- [ ] T0.4 — Configurar `pytest` e estrutura de testes em `/tests`

**Specs relacionadas:** 00-overview

---

## Fase 1 — Banco de Dados

- [ ] T1.1 — Implementar conexão SQLite com WAL mode e foreign keys (`src/db/connection.py`)
- [ ] T1.2 — Implementar modelos Peewee: `Workspace`, `Exam`, `Question`, `UserAnswer`, `Topic`, `Setting` (`src/db/models.py`)
- [ ] T1.3 — Implementar criação automática de tabelas na primeira execução
- [ ] T1.4 — Implementar índices conforme spec
- [ ] T1.5 — Implementar CASCADE DELETE em workspace e exam
- [ ] T1.6 — Testes unitários: criação de tabelas, constraints, cascade, índices

**Specs relacionadas:** 01-database-schema

---

## Fase 2 — AI Adapters

- [ ] T2.1 — Definir interface `IAIAdapter` (`src/ai/base.py`)
- [ ] T2.2 — Implementar hierarquia de exceções `AIException` (`src/ai/exceptions.py`)
- [ ] T2.3 — Implementar `OpenAIAdapter` (`src/ai/openai_adapter.py`)
- [ ] T2.4 — Implementar `GeminiAdapter` (`src/ai/gemini_adapter.py`)
- [ ] T2.5 — Implementar `ClaudeAdapter` (`src/ai/claude_adapter.py`)
- [ ] T2.6 — Implementar `OllamaAdapter` (`src/ai/ollama_adapter.py`)
- [ ] T2.7 — Implementar `AIProviderService` factory (`src/ai/provider_service.py`)
- [ ] T2.8 — Implementar backoff exponencial para rate limit
- [ ] T2.9 — Testes unitários: mocks para cada adapter, factory, exceções

**Specs relacionadas:** 09-ai-adapters

---

## Fase 3 — Storage & Config

- [ ] T3.1 — Implementar `AssetManager` para gerenciar `/data/assets/{workspace_id}/` (`src/storage/assets.py`)
- [ ] T3.2 — Implementar `FileManager` para copiar PDFs para `/data/uploads/{workspace_id}/` (`src/storage/files.py`)
- [ ] T3.3 — Implementar `ConfigService` para leitura/escrita de `settings` (`src/config/settings.py`)
- [ ] T3.4 — Implementar integração com `keyring` para credenciais (`src/config/credentials.py`)
- [ ] T3.5 — Testes unitários: asset manager, file manager, config service, credentials

**Specs relacionadas:** 01-database-schema, 02-onboarding-ai-config

---

## Fase 4 — Onboarding & Configurações de IA (UI)

- [ ] T4.1 — Implementar view de Onboarding com 5 passos (`src/ui/onboarding_view.py`)
- [ ] T4.2 — Implementar Passo 1: boas-vindas
- [ ] T4.3 — Implementar Passo 2: como funciona (cards explicativos)
- [ ] T4.4 — Implementar Passo 3: seleção de provedor (4 cards)
- [ ] T4.5 — Implementar Passo 4: campos dinâmicos de credenciais + "Testar Conexão"
- [ ] T4.6 — Implementar Passo 5: confirmação e finalização
- [ ] T4.7 — Implementar view de Configurações (alterar provedor/credenciais) (`src/ui/settings_view.py`)
- [ ] T4.8 — Implementar lógica de detecção de primeiro acesso
- [ ] T4.9 — Testes unitários: fluxo de onboarding, persistência de settings, validação de conexão

**Specs relacionadas:** 02-onboarding-ai-config

---

## Fase 5 — Workspaces (Service + UI)

- [ ] T5.1 — Implementar `WorkspaceService` (CRUD) (`src/services/workspace_service.py`)
- [ ] T5.2 — Implementar validação de unicidade de nome
- [ ] T5.3 — Implementar criação de pasta de assets ao criar workspace
- [ ] T5.4 — Implementar deleção em cascata + remoção de pasta de assets
- [ ] T5.5 — Implementar bloqueio de deleção do último workspace
- [ ] T5.6 — Implementar persistência de workspace ativo em `settings.default_workspace_id`
- [ ] T5.7 — Implementar view de listagem de workspaces com contadores (`src/ui/workspace_list_view.py`)
- [ ] T5.8 — Implementar dialog de criação/edição de workspace
- [ ] T5.9 — Implementar dialog de confirmação de deleção
- [ ] T5.10 — Testes unitários: CRUD, unicidade, cascade, bloqueio último workspace, contadores

**Specs relacionadas:** 03-workspaces

---

## Fase 6 — Upload & Ingestão de Provas (Service + UI)

- [ ] T6.1 — Implementar `ExamService` (CRUD) (`src/services/exam_service.py`)
- [ ] T6.2 — Implementar upload individual (cópia de PDF + criação de registro)
- [ ] T6.3 — Implementar upload em lote (batch queue)
- [ ] T6.4 — Implementar adição de gabarito a prova existente
- [ ] T6.5 — Implementar deleção de prova com remoção de arquivos
- [ ] T6.6 — Implementar bloqueio de deleção durante `extracting`
- [ ] T6.7 — Implementar view de listagem de provas com filtros e badges (`src/ui/exam_list_view.py`)
- [ ] T6.8 — Implementar dialog de upload individual
- [ ] T6.9 — Implementar dialog de upload em lote
- [ ] T6.10 — Implementar indicador de progresso da fila de batch
- [ ] T6.11 — Implementar view de detalhes/edição de prova
- [ ] T6.12 — Testes unitários: CRUD, upload, batch, bloqueio, deleção com arquivos

**Specs relacionadas:** 04-exam-upload-ingestion

---

## Fase 7 — Pipeline de Extração

- [ ] T7.1 — Implementar `PDFParser` com PyMuPDF (`srcpipeline/pdf_parser.py`)
- [ ] T7.2 — Implementar padrões regex para identificação de blocos de questão
- [ ] T7.3 — Implementar identificação de regiões de imagens não-textuais
- [ ] T7.4 — Implementar `ImageExtractor` com Pillow/OpenCV (`src/pipeline/image_extractor.py`)
- [ ] T7.5 — Implementar recorte de imagens em DPI 200 e salvamento como PNG
- [ ] T7.6 — Implementar `LLMExtractor` (`src/pipeline/llm_extractor.py`)
- [ ] T7.7 — Implementar prompt strategy (system + user prompt)
- [ ] T7.8 — Implementar JSON Schema de validação da resposta
- [ ] T7.9 — Implementar lógica de retries (máx 2) para respostas inválidas
- [ ] T7.10 — Implementar `PipelineOrchestrator` que coordena as 4 etapas (`src/pipeline/orchestrator.py`)
- [ ] T7.11 — Implementar execução em background (threading)
- [ ] T7.12 — Implementar atualização de `exam.status` e `exam.question_count`
- [ ] T7.13 — Implementar re-processamento (deletar questões antigas antes de re-extrair)
- [ ] T7.14 — Implementar lógica de >50% falhas → status `error`
- [ ] T7.15 — Testes unitários: PDFParser, ImageExtractor (mock), LLMExtractor (mock), orchestrator

**Specs relacionadas:** 05-question-extraction-pipeline

---

## Fase 8 — Gabarito Parser

- [ ] T8.1 — Implementar `AnswerKeyParser` (`src/pipeline/answer_key_parser.py`)
- [ ] T8.2 — Implementar extração de texto do PDF do gabarito
- [ ] T8.3 — Implementar Strategy 1: padrões regex para mapeamento questão → resposta
- [ ] T8.4 — Implementar validação de 70% de cobertura do regex
- [ ] T8.5 — Implementar Strategy 2: LLM fallback com JSON Schema
- [ ] T8.6 — Implementar `Linker`: vincular respostas às questões no banco
- [ ] T8.7 — Implementar atualização de `correct_answer` e `is_answerable`
- [ ] T8.8 — Implementar atualização de `exam.has_answer_key = True`
- [ ] T8.9 — Implementar enfileiramento se prova estiver em `extracting`
- [ ] T8.10 — Implementar re-processamento de gabarito
- [ ] T8.11 — Testes unitários: regex patterns, LLM fallback (mock), linker, atualização de status

**Specs relacionadas:** 06-answer-key-parser

---

## Fase 9 — Aba Tópicos (Service + UI)

- [ ] T9.1 — Implementar `TopicService` com queries de agregação (`src/services/topic_service.py`)
- [ ] T9.2 — Implementar query de incidência por tópico (workspace)
- [ ] T9.3 — Implementar query de desempenho por tópico (workspace)
- [ ] T9.4 — Implementar atualização da tabela `topics` após extração/deleção
- [ ] T9.5 — Implementar view de Lista de Tópicos (incidência) (`src/ui/topics_view.py`)
- [ ] T9.6 — Implementar view de Desempenho por Tópico
- [ ] T9.7 — Implementar view de Relatório Sintético (resumo + gráficos)
- [ ] T9.8 — Implementar filtros (todas as provas / prova específica)
- [ ] T9.9 — Implementar ordenação (por questões / alfabética)
- [ ] T9.10 — Implementar indicadores visuais coloridos (verde/amarelo/vermelho)
- [ ] T9.11 — Testes unitários: queries de agregação, atualização de topics, agrupamento "Tópico não identificado"

**Specs relacionadas:** 07-topics-analytics

---

## Fase 10 — Aba Questões / Simulado (Service + UI)

- [ ] T10.1 — Implementar `QuestionService` (`src/services/question_service.py`)
- [ ] T10.2 — Implementar filtro de questões `is_answerable = True`
- [ ] T10.3 — Implementar carregamento por modo (aleatório / por tópico / por prova)
- [ ] T10.4 — Implementar embaralhamento de questões e alternativas
- [ ] T10.5 — Implementar lógica de não-repetição na mesma sessão
- [ ] T10.6 — Implementar persistência de resposta em `user_answers`
- [ ] T10.7 — Implementar view de configuração de sessão (`src/ui/practice_config_view.py`)
- [ ] T10.8 — Implementar view de questão (enunciado, imagens, alternativas) (`src/ui/practice_question_view.py`)
- [ ] T10.9 — Implementar feedback imediato (cores, destaque correto/incorreto)
- [ ] T10.10 — Implementar view de resumo da sessão (`src/ui/practice_summary_view.py`)
- [ ] T10.11 — Implementar estados vazios (sem questões answerable)
- [ ] T10.12 — Testes unitários: filtros, modos, embaralhamento, não-repetição, persistência, feedback

**Specs relacionadas:** 08-questions-practice

---

## Fase 11 — Navegação & Shell da Aplicação

- [ ] T11.1 — Implementar shell principal com navigation rail/bar (Workspaces, Provas, Questões, Tópicos, Configurações)
- [ ] T11.2 — Implementar roteamento entre views
- [ ] T11.3 — Implementar estado global (workspace ativo, configurações)
- [ ] T11.4 — Implementar `main.py` com inicialização do Flet e roteamento
- [ ] T11.5 — Testes de integração: fluxo completo (onboarding → criar workspace → upload prova → extrair → adicionar gabarito → praticar)

**Specs relacionadas:** 00-overview

---

## Fase 12 — Polish & Testes Finais

- [ ] T12.1 — Revisar todos os critérios de aceitação de cada spec
- [ ] T12.2 — Garantir 90% de cobertura de testes unitários
- [ ] T12.3 — Testar com PDFs reais de provas (diversos formatos)
- [ ] T12.4 — Validar performance (tempos das NFRs)
- [ ] T12.5 — Validar compatibilidade cross-platform (Windows/macOS/Linux)
- [ ] T12.6 — Review final (Review Agent)

**Specs relacionadas:** Todas
