# Spec 01 — Modelo de Dados (Database Schema)

## Objetivo

Definir o esquema completo do banco de dados SQLite, incluindo tabelas, relacionamentos, índices, constraints e configurações de WAL mode.

## Contexto

O banco SQLite é a única fonte de persistência estruturada da aplicação. Ele armazena workspaces, provas, questões, gabaritos, respostas do usuário, tópicos, configurações e credenciais de IA. O ORM utilizado é Peewee.

## Configuração do Banco

- **Engine:** SQLite
- **WAL Mode:** Habilitado na conexão (`PRAGMA journal_mode=WAL`)
- **Foreign Keys:** Habilitadas (`PRAGMA foreign_keys=ON`)
- **Arquivo:** `/data/app.db`
- **ORM:** Peewee

## Tabelas

### `workspaces`

| Coluna       | Tipo         | Constraints              | Descrição                          |
|--------------|--------------|--------------------------|-------------------------------------|
| id           | Integer      | PK, Auto-increment       | Identificador único                 |
| name         | TextField    | NOT NULL                 | Nome do workspace                   |
| description  | TextField    | NULL                     | Descrição opcional                  |
| created_at   | DateTime     | NOT NULL, default=now    | Data de criação                     |
| updated_at   | DateTime     | NOT NULL, default=now    | Data de última atualização          |

### `exams`

| Coluna         | Tipo         | Constraints                    | Descrição                              |
|----------------|--------------|--------------------------------|----------------------------------------|
| id             | Integer      | PK, Auto-increment             | Identificador único                    |
| workspace_id   | Integer      | FK → workspaces.id, NOT NULL   | Workspace a que pertence               |
| title          | TextField    | NOT NULL                       | Título da prova                        |
| exam_date      | DateField    | NULL                           | Data da prova (opcional)               |
| source_pdf_path| TextField    | NOT NULL                       | Caminho do PDF da prova                |
| answer_key_pdf_path | TextField | NULL                          | Caminho do PDF do gabarito (opcional)  |
| has_answer_key | BooleanField | NOT NULL, default=False        | Indica se gabarito foi processado      |
| status         | TextField    | NOT NULL, default='pending'    | Status de ingestão: pending/extracting/completed/error |
| question_count | IntegerField | NULL                           | Número de questões extraídas           |
| created_at     | DateTime     | NOT NULL, default=now          | Data de criação                        |
| updated_at     | DateTime     | NOT NULL, default=now          | Data de última atualização             |

**Constraints:**
- `status` deve ser um dos valores: `pending`, `extracting`, `completed`, `error`.
- Índice em `(workspace_id, status)`.

### `questions`

| Coluna          | Tipo         | Constraints                     | Descrição                                     |
|-----------------|--------------|---------------------------------|------------------------------------------------|
| id              | Integer      | PK, Auto-increment              | Identificador único                            |
| exam_id         | Integer      | FK → exams.id, NOT NULL         | Prova de origem                               |
| question_number | IntegerField | NOT NULL                        | Número da questão na prova                     |
| statement       | TextField    | NOT NULL                        | Enunciado completo                             |
| question_type   | TextField    | NOT NULL                        | Tipo: `multiple_choice` ou `true_false`        |
| options         | JSONField    | NOT NULL                        | Alternativas: `{"A": "...", "B": "..."}` ou `{"C": "Certo", "E": "Errado"}` |
| correct_answer  | TextField    | NULL                            | Resposta correta (A/B/C/D/E ou C/E)            |
| topic_primary   | TextField    | NULL                            | Tópico/matéria principal identificado          |
| topic_secondary | TextField    | NULL                            | Tópico secundário (opcional)                   |
| image_paths     | JSONField    | NULL                            | Lista de caminhos de imagens recortadas: `["assets/1/42_0.png"]` |
| page_number     | IntegerField | NULL                            | Página do PDF onde a questão foi encontrada    |
| is_answerable   | BooleanField | NOT NULL, default=False         | True se a prova tem gabarito processado         |
| created_at      | DateTime     | NOT NULL, default=now           | Data de criação                                |

**Constraints:**
- UNIQUE `(exam_id, question_number)` — não permite questões duplicadas na mesma prova.
- `question_type` deve ser `multiple_choice` ou `true_false`.
- `correct_answer` é NULL até que o gabarito seja processado.
- `is_answerable` = True quando `correct_answer` não é NULL.
- Índice em `(exam_id)`.
- Índice em `(topic_primary)`.

### `user_answers`

| Coluna        | Tipo         | Constraints                     | Descrição                                |
|---------------|--------------|---------------------------------|------------------------------------------|
| id            | Integer      | PK, Auto-increment              | Identificador único                      |
| question_id   | Integer      | FK → questions.id, NOT NULL     | Questão respondida                       |
| user_answer   | TextField    | NOT NULL                        | Resposta dada pelo usuário               |
| is_correct    | BooleanField | NOT NULL                        | Se acertou ou errou                      |
| answered_at   | DateTime     | NOT NULL, default=now           | Momento da resposta                      |

**Constraints:**
- Índice em `(question_id)`.
- Índice em `(answered_at)`.

### `topics`

| Coluna        | Tipo         | Constraints                     | Descrição                                |
|---------------|--------------|---------------------------------|------------------------------------------|
| id            | Integer      | PK, Auto-increment              | Identificador único                      |
| workspace_id  | Integer      | FK → workspaces.id, NOT NULL    | Workspace de referência                  |
| name          | TextField    | NOT NULL                        | Nome do tópico/matéria                   |
| question_count| IntegerField | NOT NULL, default=0             | Número de questões associadas            |
| created_at    | DateTime     | NOT NULL, default=now           | Data de criação                          |

**Constraints:**
- UNIQUE `(workspace_id, name)` — não permite tópicos duplicados no mesmo workspace.
- Índice em `(workspace_id)`.

> **Nota:** A tabela `topics` é uma view materializada / agregação derivada de `questions.topic_primary`. Pode ser populada via trigger ou reconstruída sob demanda. O `question_count` reflete questões cujo `topic_primary` corresponde ao `name`.

### `settings`

| Coluna        | Tipo         | Constraints                     | Descrição                                |
|---------------|--------------|---------------------------------|------------------------------------------|
| id            | Integer      | PK, Auto-increment              | Identificador único                      |
| key           | TextField    | NOT NULL, UNIQUE                | Chave da configuração                    |
| value         | TextField    | NULL                            | Valor da configuração                    |
| is_encrypted  | BooleanField | NOT NULL, default=False         | Indica se o valor está cifrado           |
| updated_at    | DateTime     | NOT NULL, default=now           | Data de última atualização               |

**Chaves esperadas:**
- `onboarding_completed` — booleano (string `"true"`/`"false"`)
- `ai_provider` — `"openai"` | `"gemini"` | `"claude"` | `"ollama"`
- `ai_api_key` — armazenado cifrado OU via `keyring` do SO (preferencial)
- `ai_model` — modelo selecionado (ex: `"gpt-4o"`, `"gemini-1.5-pro"`)
- `ai_endpoint` — URL para Ollama local (ex: `"http://localhost:11434"`)
- `default_workspace_id` — ID do último workspace ativo

## Diagrama de Relacionamentos

```
workspaces (1) ──── (N) exams
workspaces (1) ──── (N) topics
exams (1) ──────── (N) questions
questions (1) ───── (N) user_answers
```

## Regras de Negócio

1. **CASCADE DELETE:** Ao deletar um workspace, deletar em cascata exams, questions, user_answers e topics associados.
2. **CASCADE DELETE:** Ao deletar um exam, deletar em cascata questions e user_answers associados.
3. **Integridade de gabarito:** O campo `questions.is_answerable` é atualizado para `True` apenas quando `questions.correct_answer` recebe um valor válido.
4. **Isolamento de workspace:** Todas as queries de UI devem filtrar por `workspace_id` ativo.
5. **Backup:** A função de backup copia o arquivo `app.db` para um destino escolhido pelo usuário.

## Casos de Erro

| ID    | Cenário                                        | Comportamento                                     |
|-------|------------------------------------------------|---------------------------------------------------|
| ERR-DB-01 | Falha ao abrir conexão com SQLite           | Exibir mensagem de erro e encerrar aplicação      |
| ERR-DB-02 | Violação de UNIQUE constraint                | Retornar erro de validação amigável               |
| ERR-DB-03 | Falha ao ativar WAL mode                    | Logar warning, continuar com journal mode default |
| ERR-DB-04 | Arquivo app.db corrompido                   | Oferecer restauração de backup se disponível      |

## Critérios de Aceitação

1. O banco SQLite é criado automaticamente na primeira execução se não existir.
2. WAL mode é ativado na conexão.
3. Foreign keys são enforcement habilitado.
4. Todas as tabelas possuem as colunas e tipos conforme especificado.
5. CASCADE DELETE funciona ao deletar workspace e exam.
6. Índices são criados nas colunas especificadas.
7. Constraint UNIQUE `(exam_id, question_number)` impede duplicação.
8. Constraint UNIQUE `(workspace_id, name)` em topics impede duplicação.

## Fora de Escopo

- Migrações versionadas (schema é criado do zero na primeira execução).
- Réplicas ou sharding.
- Banco em rede (apenas arquivo local).
