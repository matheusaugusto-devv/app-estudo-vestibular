# Spec 07 — Tópicos (Relatórios & Analytics)

## Objetivo

Definir a aba de Tópicos, que oferece uma visão consolidada dos tópicos/matérias identificados nas questões extraídas, com relatórios de incidência e analytics de desempenho.

## Contexto

Após a extração, cada questão possui um `topic_primary` (e opcionalmente `topic_secondary`) identificado pelo LLM. A aba Tópicos agrega esses dados para o usuário entender quais conteúdos são mais cobrados em cada prova ou workspace, além de visualizar seu desempenho por tópico.

## Regras de Negócio

1. A aba Tópicos exibe dados apenas do workspace ativo.
2. Tópicos são derivados de `questions.topic_primary` — agregados por workspace.
3. A tabela `topics` mantém um cache/agregação: `name`, `workspace_id`, `question_count`.
4. A agregação de tópicos é atualizada quando:
   - Uma prova é processada (questões extraídas).
   - Uma prova é deletada.
   - Uma questão é re-processada.
5. O relatório de incidência mostra: tópico, número de questões, percentual sobre o total.
6. O relatório de desempenho mostra: tópico, total respondidas, acertos, erros, taxa de acerto.
7. Tópicos sem questões respondidas ainda aparecem na listagem de incidência mas com desempenho "—".
8. O usuário pode filtrar por prova específica ou ver consolidado do workspace inteiro.

## Views da Aba Tópicos

### View 1 — Lista de Tópicos (Incidência)
- Tabela ou lista de cards exibindo:
  - Nome do tópico
  - Número de questões (badge)
  - Percentual de incidência (barra de progresso relativa)
  - Número de provas que cobrem o tópico
- Ordenação: por número de questões (decrescente) ou alfabética.
- Filtro: todas as provas / prova específica (dropdown).

### View 2 — Desempenho por Tópico
- Tabela exibindo:
  - Nome do tópico
  - Total respondidas
  - Acertos (com ícone verde)
  - Erros (com ícone vermelho)
  - Taxa de acerto (% com barra colorida: verde >70%, amarelo 50-70%, vermelho <50%)
- Ordenação: por taxa de acerto (crescente para identificar pontos fracos) ou alfabética.
- Filtro: todas as provas / prova específica.

### View 3 — Relatório Sintético (Resumo do Workspace)
- Card de resumo com:
  - Total de questões no workspace
  - Total de tópicos distintos
  - Tópico com maior incidência
  - Tópico com menor taxa de acerto (ponto fraco)
  - Taxa de acerto geral do workspace
- Gráfico de barras horizontal: top 10 tópicos por incidência.
- Gráfico de barras horizontal: top 10 tópicos com menor taxa de acerto.

## Queries de Agregação

### Incidência por Tópico (Workspace)
```sql
SELECT topic_primary, COUNT(*) as question_count
FROM questions
JOIN exams ON questions.exam_id = exams.id
WHERE exams.workspace_id = ?
GROUP BY topic_primary
ORDER BY question_count DESC;
```

### Desempenho por Tópico (Workspace)
```sql
SELECT q.topic_primary,
  COUNT(ua.id) as total_answered,
  SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count,
  SUM(CASE WHEN ua.is_correct = 0 THEN 1 ELSE 0 END) as wrong_count
FROM questions q
JOIN exams e ON q.exam_id = e.id
LEFT JOIN user_answers ua ON ua.question_id = q.id
WHERE e.workspace_id = ?
GROUP BY q.topic_primary;
```

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-TP-01 | Listar tópicos do workspace ativo com contagem de questões                  |
| FR-TP-02 | Exibir percentual de incidência por tópico                                  |
| FR-TP-03 | Permitir ordenação por número de questões ou alfabética                     |
| FR-TP-04 | Permitir filtro por prova específica ou todas                              |
| FR-TP-05 | Exibir desempenho por tópico (acertos, erros, taxa)                        |
| FR-TP-06 | Exibir taxa de acerto com indicador visual colorido                        |
| FR-TP-07 | Exibir relatório sintético do workspace (resumo)                            |
| FR-TP-08 | Exibir gráfico de top 10 tópicos por incidência                             |
| FR-TP-09 | Exibir gráfico de top 10 tópicos com menor taxa de acerto                  |
| FR-TP-10 | Atualizar agregação de tópicos após extração/deleção de prova              |
| FR-TP-11 | Exibir "—" para tópicos sem respostas no desempenho                        |
| FR-TP-12 | Exibir número de provas que cobrem cada tópico                             |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-TP-01 | Queries de agregação devem executar em < 500ms                         |
| NFR-TP-02 | Gráficos renderizados com componentes nativos do Flet (sem libs JS)     |
| NFR-TP-03 | Atualização da tabela `topics` não deve bloquear a UI                   |

## Casos de Erro

| ID    | Cenário                                           | Comportamento                                          |
|-------|---------------------------------------------------|--------------------------------------------------------|
| ERR-TP-01 | Workspace sem provas/questões                  | Exibir estado vazio: "Nenhuma questão encontrada."     |
| ERR-TP-02 | Questão sem `topic_primary` (NULL)             | Agrupar em "Tópico não identificado"                   |
| ERR-TP-03 | Falha ao atualizar tabela `topics`             | Logar warning; dados ainda disponíveis via query direta |

## Critérios de Aceitação

1. A aba Tópicos lista todos os tópicos do workspace ativo com contagem de questões.
2. O percentual de incidência é exibido por tópico com barra de progresso.
3. O usuário pode ordenar por número de questões ou alfabeticamente.
4. O usuário pode filtrar por prova específica ou ver consolidado.
5. O desempenho por tópico exibe acertos, erros e taxa de acerto.
6. A taxa de acerto tem indicador visual colorido (verde/amarelo/vermelho).
7. O relatório sintético exibe resumo do workspace (total, tópicos, maior incidência, ponto fraco).
8. Gráficos de top 10 por incidência e por menor taxa de acerto são exibidos.
9. Tópicos sem respostas exibem "—" no desempenho.
10. A agregação é atualizada após extração ou deleção de provas.
11. Questões sem `topic_primary` são agrupadas em "Tópico não identificado".

## Fora de Escopo

- Geração de relatório em PDF exportável.
- Recomendação de estudo personalizada por IA.
- Comparação de tópicos entre workspaces diferentes.
- Histórico temporal de evolução de desempenho (gráfico de linha temporal).
- Edição manual de tópicos (renomear, fundir tópicos).
