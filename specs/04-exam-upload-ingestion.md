# Spec 04 — Upload & Ingestão de Provas e Gabaritos

## Objetivo

Definir o fluxo de upload de PDFs de provas e gabaritos, o gerenciamento de filas de ingestão (batch queue) e o CRUD completo de provas.

## Contexto

O usuário faz upload de PDFs de provas para um workspace. Cada prova pode ter um PDF de gabarito separado (opcional). A prova passa por um pipeline de extração que estrutura as questões. Sem gabarito, as questões são extraídas mas ficam bloqueadas para prática.

## Fluxo de Upload

### Upload Individual
1. Usuário seleciona "Adicionar Prova" no workspace ativo.
2. Dialog exibe campos:
   - **Título da prova** (obrigatório)
   - **Data da prova** (opcional, date picker)
   - **PDF da prova** (file picker, obrigatório)
   - **PDF do gabarito** (file picker, opcional)
3. Ao confirmar, o PDF é copiado para `/data/uploads/{workspace_id}/`.
4. Um registro de `exam` é criado com `status = 'pending'`.
5. O pipeline de extração é iniciado (ver Spec 05).

### Upload em Lote (Batch Queue)
1. Usuário seleciona "Adicionar Múltiplas Provas".
2. File picker permite selecionar múltiplos PDFs de uma vez.
3. Para cada PDF, um dialog rápido solicita:
   - Título (pré-preenchido com o nome do arquivo)
   - Data (opcional)
   - PDF do gabarito (opcional, pode ser marcado "Sem gabarito")
4. Todos os exams são criados com `status = 'pending'`.
5. A fila de ingestão processa as provas sequencialmente.
6. Um indicador de progresso exibe: "Processando prova 2 de 5..." com barra de progresso por prova.

## Regras de Negócio

1. O título da prova é obrigatório.
2. O PDF da prova é obrigatório; o PDF do gabarito é opcional.
3. Uma prova sem gabarito tem `has_answer_key = False` — suas questões são extraídas mas `is_answerable = False`.
4. Uma prova com gabarito tem `has_answer_key = True` após o processamento do gabarito (ver Spec 06).
5. O `status` da prova segue o ciclo: `pending` → `extracting` → `completed` (ou `error`).
6. O PDF original é copiado para `/data/uploads/{workspace_id}/` — não é modificado.
7. É possível fazer upload do gabarito posteriormente (prova criada sem gabarito pode receber um depois).
8. Ao adicionar gabarito a uma prova existente, o pipeline de gabarito é executado (Spec 06) e `has_answer_key` é atualizado para `True`.
9. Ao deletar uma prova, o PDF original e os assets extraídos são removidos do disco.
10. Não é possível deletar uma prova durante o status `extracting`.

## CRUD de Provas

### Listar
- Exibir todas as provas do workspace ativo.
- Cada item exibe: título, data, status (badge colorido), número de questões, indicador de gabarito (ícone check/xis).
- Filtro por status (todas / pendentes / processadas / com erro).

### Editar
- Editar título, data e adicionar/remover gabarito.
- Não é possível editar durante `extracting`.

### Deletar
- Confirmação: "Deletar prova '{title}'? Todas as questões e registros serão removidos."
- Remove registro, PDFs e assets associados.

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-EX-01 | Permitir upload individual de prova com PDF obrigatório e gabarito opcional |
| FR-EX-02 | Permitir upload em lote com múltiplos PDFs                                  |
| FR-EX-03 | Copiar PDFs para `/data/uploads/{workspace_id}/`                           |
| FR-EX-04 | Criar registro de exam com `status = 'pending'`                             |
| FR-EX-05 | Iniciar pipeline de extração automaticamente após criação                  |
| FR-EX-06 | Exibir progresso da fila de ingestão (batch)                                |
| FR-EX-07 | Listar provas do workspace com filtros por status                           |
| FR-EX-08 | Editar título e data da prova                                               |
| FR-EX-09 | Adicionar gabarito a prova existente (sem gabarito)                        |
| FR-EX-10 | Deletar prova com confirmação e remoção de arquivos                        |
| FR-EX-11 | Bloquear deleção durante status `extracting`                               |
| FR-EX-12 | Exibir badge de status colorido por prova                                  |
| FR-EX-13 | Exibir indicador visual de presença/ausência de gabarito                   |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-EX-01 | PDFs suportados: qualquer versão de PDF válida                          |
| NFR-EX-02 | Tamanho máximo de PDF: 100MB                                             |
| NFR-EX-03 | A fila de batch processa provas sequencialmente (não paralelo)          |
| NFR-EX-04 | Interface permanece responsiva durante extração (threading/async)       |

## Casos de Erro

| ID    | Cenário                                           | Comportamento                                            |
|-------|---------------------------------------------------|----------------------------------------------------------|
| ERR-EX-01 | PDF corrompido ou inválido                     | Status = `error`; mensagem: "PDF inválido ou corrompido." |
| ERR-EX-02 | PDF excede 100MB                               | Bloquear upload; mensagem: "Tamanho máximo: 100MB."      |
| ERR-EX-03 | Falha no pipeline de extração                  | Status = `error`; permitir re-tentar                     |
| ERR-EX-04 | Tentar deletar durante `extracting`            | Mensagem: "Aguarde a conclusão do processamento."        |
| ERR-EX-05 | Falha ao copiar PDF para storage               | Mensagem: "Erro ao salvar arquivo. Tente novamente."     |
| ERR-EX-06 | Título vazio                                   | Mensagem: "O título da prova é obrigatório."             |

## Critérios de Aceitação

1. O usuário pode fazer upload individual de uma prova com título, data e PDF obrigatório.
2. O usuário pode fazer upload de um PDF de gabarito opcional junto com a prova.
3. O usuário pode fazer upload em lote de múltiplos PDFs.
4. Os PDFs são copiados para `/data/uploads/{workspace_id}/`.
5. Um registro de exam é criado com `status = 'pending'` para cada prova.
6. O pipeline de extração inicia automaticamente após a criação.
7. A fila de batch exibe progresso por prova.
8. A listagem de provas exibe título, data, status, número de questões e indicador de gabarito.
9. O usuário pode editar título e data de uma prova.
10. O usuário pode adicionar gabarito a uma prova existente sem gabarito.
11. O usuário pode deletar uma prova com confirmação, removendo registros e arquivos.
12. Não é possível deletar uma prova durante `extracting`.
13. Provas com erro podem ser re-processadas.
14. PDFs acima de 100MB são rejeitados.

## Fora de Escopo

- Download de PDFs de fontes online (URL).
- OCR de PDFs digitalizados como imagens (escaneados) — suporte inicial apenas para PDFs com texto extraível + identificação de elementos visuais.
- Comparação automática entre duas provas.
- Versionamento de PDFs atualizados da mesma prova.
