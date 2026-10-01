# Spec 08 — Questões (Módulo Prático / Simulado)

## Objetivo

Definir o módulo de prática/simulado onde o usuário responde questões de forma randômica ou filtrada, recebe feedback imediato e tem seu desempenho registrado.

## Contexto

Esta é a aba principal de estudo ativo. O usuário interage com questões extraídas, respondendo e recebendo feedback. Questões de provas sem gabarito processado são bloqueadas neste módulo.

## Regras de Negócio

1. **Bloqueio de questões sem gabarito:** Apenas questões com `is_answerable = True` são exibidas neste módulo. Questões de provas sem gabarito processado (`has_answer_key = False`) não aparecem.
2. **Modos de prática:**
   - **Aleatório:** Questões embaralhadas do workspace ou filtro selecionado.
   - **Por tópico:** Questões filtradas por `topic_primary`.
   - **Por prova:** Questões filtradas por `exam_id`.
3. **Feedback imediato:** Após responder, o usuário vê se acertou ou errou, qual era a resposta correta e o enunciado novamente.
4. **Registro de desempenho:** Cada resposta é persistida em `user_answers` (resposta dada, se acertou, timestamp).
5. **Sem repetição imediata:** Uma questão respondida recentemente (na mesma sessão) tem menor prioridade de reaparecer.
6. **Navegação:** O usuário pode avançar para a próxima questão ou parar a sessão a qualquer momento.
7. **Sessão de prática:** Um conjunto de questões é carregado por sessão. O usuário define quantas questões quer responder (padrão: 10).
8. **Resumo da sessão:** Ao finalizar, exibe total respondidas, acertos, erros e taxa de acerto.

## Fluxo de Uso

### Passo 1 — Configuração da Sessão
- Dialog exibe opções:
  - **Modo:** Aleatório / Por tópico / Por prova
  - **Filtro:** (condicional ao modo)
    - Por tópico: dropdown de tópicos disponíveis
    - Por prova: dropdown de provas disponíveis
  - **Número de questões:** input numérico (padrão 10, máximo = total disponível)
- Botão "Iniciar".

### Passo 2 — Responder Questões
- Exibição da questão:
  - Número da questão e prova de origem (badge)
  - Tópico (tag)
  - Enunciado completo (texto formatado)
  - Imagens/gráficos recortados (se houver) — exibidos abaixo do enunciado
  - Alternativas interativas (radio buttons ou cards clicáveis)
    - `multiple_choice`: A, B, C, D, E
    - `true_false`: Certo, Errado
- Botão "Confirmar Resposta" (habilitado após selecionar uma alternativa).

### Passo 3 — Feedback
- Após confirmar:
  - Se correta: banner verde "Resposta Correta!"
  - Se incorreta: banner vermelho "Resposta Incorreta"
  - Exibir a alternativa correta destacada em verde
  - A alternativa selecionada pelo usuário destacada em vermelho (se incorreta)
- Botões: "Próxima Questão" / "Finalizar Sessão"
- Persistir resposta em `user_answers`.

### Passo 4 — Resumo da Sessão
- Ao finalizar (ou ao completar todas as questões):
  - Total respondidas
  - Acertos (número + percentual)
  - Erros (número + percentual)
  - Taxa de acerto geral
  - Lista de tópicos abordados na sessão com mini-desempenho
- Botões: "Nova Sessão" / "Voltar ao Início"

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-QP-01 | Exibir apenas questões com `is_answerable = True`                          |
| FR-QP-02 | Bloquear questões de provas sem gabarito (`has_answer_key = False`)        |
| FR-QP-03 | Oferecer 3 modos: Aleatório, Por tópico, Por prova                         |
| FR-QP-04 | Permitir configurar número de questões por sessão (padrão 10)              |
| FR-QP-05 | Carregar conjunto de questões conforme modo e filtro selecionado           |
| FR-QP-06 | Exibir enunciado, imagens recortadas e alternativas                        |
| FR-QP-07 | Alternativas como radio buttons/cards interativos                          |
| FR-QP-08 | Diferenciar `multiple_choice` (A-E) e `true_false` (Certo/Errado)         |
| FR-QP-09 | Exibir feedback imediato (correto/incorreto) após confirmar                |
| FR-QP-10 | Destacar alternativa correta em verde e incorreta em vermelho             |
| FR-QP-11 | Persistir resposta em `user_answers` (answer, is_correct, timestamp)      |
| FR-QP-12 | Permitir avançar para próxima questão ou finalizar sessão                  |
| FR-QP-13 | Exibir resumo da sessão ao finalizar                                       |
| FR-QP-14 | Resumo com acertos, erros, taxa de acerto e tópicos abordados             |
| FR-QP-15 | Embaralhar ordem das questões no modo aleatório                            |
| FR-QP-16 | Embaralhar ordem das alternativas (opcional, default ON)                  |
| FR-QP-17 | Não repetir questão já respondida na mesma sessão                          |
| FR-QP-18 | Exibir número da questão atual / total (ex: "Questão 3 de 10")            |
| FR-QP-19 | Exibir prova de origem e tópico como badges/tags                          |
| FR-QP-20 | Exibir imagens recortadas abaixo do enunciado quando existirem            |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-QP-01 | Carregamento da sessão deve ser < 1 segundo                            |
| NFR-QP-02 | Feedback visual deve aparecer em < 200ms após confirmar                |
| NFR-QP-03 | Imagens recortadas carregadas do disco local (sem latência de rede)    |
| NFR-QP-04 | UI permanece responsiva durante carregamento de imagens                |

## Casos de Erro

| ID    | Cenário                                               | Comportamento                                            |
|-------|-------------------------------------------------------|----------------------------------------------------------|
| ERR-QP-01 | Nenhuma questão answerable no workspace            | Exibir: "Nenhuma questão disponível. Adicione provas com gabarito." |
| ERR-QP-02 | Tópico selecionado sem questões answerable         | Exibir: "Nenhuma questão disponível para este tópico."   |
| ERR-QP-03 | Número solicitado > questões disponíveis           | Ajustar para o total disponível; informar usuário        |
| ERR-QP-04 | Falha ao carregar imagem recortada                 | Exibir placeholder "Imagem indisponível"                 |
| ERR-QP-05 | Falha ao persistir resposta no banco               | Logar erro; exibir warning; permitir continuar           |
| ERR-QP-06 | Sessão iniciada mas provas em extração             | Questões em extração não aparecem (filtro por is_answerable) |

## Critérios de Aceitação

1. Apenas questões com `is_answerable = True` são exibidas no módulo.
2. Questões de provas sem gabarito não aparecem.
3. O usuário pode escolher entre 3 modos: Aleatório, Por tópico, Por prova.
4. O usuário pode definir o número de questões (padrão 10).
5. A questão exibe enunciado, imagens recortadas e alternativas.
6. Alternativas são interativas (radio buttons ou cards).
7. `multiple_choice` exibe A-E; `true_false` exibe Certo/Errado.
8. Após confirmar, feedback imediato é exibido (correto/incorreto).
9. A alternativa correta é destacada em verde; a incorreta selecionada em vermelho.
10. Cada resposta é persistida em `user_answers`.
11. O usuário pode avançar ou finalizar a sessão.
12. O resumo da sessão exibe acertos, erros, taxa de acerto e tópicos.
13. No modo aleatório, as questões são embaralhadas.
14. Questões já respondidas na sessão não se repetem.
15. O indicador "Questão X de Y" é exibido.
16. Se não há questões answerable, mensagem apropriada é exibida.

## Fora de Escopo

- Modo cronometrado (timer) — futura melhoria.
- Modo simulado completo (prova inteira com tempo limitado).
- Exportação de resultados da sessão.
- Comparação de desempenho entre sessões.
- Modo revisão (revisar apenas questões erradas anteriormente) — futura melhoria.
- Peso/dificuldade das questões.
