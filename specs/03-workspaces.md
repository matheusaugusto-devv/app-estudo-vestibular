# Spec 03 — Workspaces

## Objetivo

Definir o CRUD completo de Workspaces, que são unidades de isolamento lógico para organizar provas, questões e tópicos por concurso/exame.

## Contexto

Cada Workspace representa um contexto de estudo (ex: "Concurso Banco do Brasil", "ENEM 2024", "Residência Médica"). Todas as provas, questões, respostas e tópicos pertencem a um workspace. Não há compartilhamento de dados entre workspaces.

## Regras de Negócio

1. Um workspace deve ter um nome único (não permite dois workspaces com o mesmo nome).
2. A descrição é opcional.
3. Ao criar um workspace, uma pasta de assets é criada: `/data/assets/{workspace_id}/`.
4. Ao deletar um workspace, todos os registros relacionados (exams, questions, user_answers, topics) são deletados em cascata (CASCADE DELETE).
5. Ao deletar um workspace, os arquivos de assets associados (`/data/assets/{workspace_id}/`) também são removidos.
6. O workspace ativo é persistido em `settings.default_workspace_id`.
7. Não é possível deletar o último workspace restante — deve haver pelo menos 1.
8. O nome do workspace é limitado a 100 caracteres.

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-WS-01 | Listar todos os workspaces em ordem de criação (mais recente primeiro)     |
| FR-WS-02 | Criar novo workspace com nome (obrigatório) e descrição (opcional)         |
| FR-WS-03 | Validar unicidade do nome do workspace                                     |
| FR-WS-04 | Editar nome e descrição de um workspace existente                          |
| FR-WS-05 | Deletar workspace com confirmação (dialog de confirmação)                  |
| FR-WS-06 | Ao deletar, remover em cascata provas, questões, respostas e tópicos       |
| FR-WS-07 | Ao deletar, remover pasta de assets do workspace                           |
| FR-WS-08 | Impedir deleção do último workspace restante                               |
| FR-WS-09 | Definir workspace ativo ao clicar/selecionar                               |
| FR-WS-10 | Persistir workspace ativo em `settings.default_workspace_id`              |
| FR-WS-11 | Exibir contador de provas e questões por workspace na listagem            |
| FR-WS-12 | Criar pasta `/data/assets/{workspace_id}/` ao criar workspace             |

## Interface de Usuário

### Tela de Listagem de Workspaces
- Grid ou lista de cards, cada card exibindo:
  - Nome do workspace
  - Descrição (se houver)
  - Contador de provas (ex: "5 provas")
  - Contador de questões (ex: "150 questões")
  - Botões: "Abrir", "Editar", "Deletar"
- Botão flutuante "+" para criar novo workspace.

### Dialog de Criação/Edição
- Campo: Nome (obrigatório, máximo 100 caracteres)
- Campo: Descrição (opcional, textarea, máximo 500 caracteres)
- Botões: "Salvar", "Cancelar"

### Dialog de Confirmação de Deleção
- Texto: "Tem certeza que deseja deletar o workspace '{name}'? Todas as provas, questões e registros serão removidos permanentemente."
- Botões: "Deletar", "Cancelar"

## Casos de Erro

| ID    | Cenário                                         | Comportamento                                          |
|-------|-------------------------------------------------|--------------------------------------------------------|
| ERR-WS-01 | Tentar criar workspace com nome vazio        | Mensagem: "O nome do workspace é obrigatório."         |
| ERR-WS-02 | Tentar criar workspace com nome duplicado    | Mensagem: "Já existe um workspace com este nome."      |
| ERR-WS-03 | Nome exceder 100 caracteres                  | Input bloqueia além do limite                          |
| ERR-WS-04 | Tentar deletar último workspace              | Mensagem: "Não é possível deletar o único workspace."  |
| ERR-WS-05 | Falha ao criar pasta de assets               | Logar erro, exibir warning, workspace ainda é criado   |

## Critérios de Aceitação

1. O usuário pode criar um workspace com nome e descrição opcional.
2. Não é possível criar dois workspaces com o mesmo nome.
3. O usuário pode editar o nome e descrição de um workspace.
4. O usuário pode deletar um workspace com diálogo de confirmação.
5. Ao deletar, provas, questões, respostas e tópicos associados são removidos.
6. Ao deletar, a pasta de assets do workspace é removida.
7. Não é possível deletar o último workspace restante.
8. A listagem exibe contadores de provas e questões por workspace.
9. O workspace ativo é persistido e restaurado ao reabrir a aplicação.
10. A pasta `/data/assets/{workspace_id}/` é criada ao criar um workspace.

## Fora de Escopo

- Compartilhamento de workspaces entre usuários.
- Workspaces em nuvem.
- Exportação/importação de workspace individual.
- Arquivamento de workspaces (soft delete).
