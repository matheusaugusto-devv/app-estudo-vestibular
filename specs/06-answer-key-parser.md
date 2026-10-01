# Spec 06 — Gabarito Parser

## Objetivo

Definir o processamento do PDF do gabarito separado para extrair o mapeamento `[Número da Questão] → [Resposta Correta]` e vincular automaticamente com as questões cadastradas da respectiva prova.

## Contexto

O gabarito é um PDF separado da prova que contém as respostas corretas. Após o processamento do gabarito, as questões da prova ficam desbloqueadas (`is_answerable = True`) para o módulo de prática/simulado. O gabarito pode ser enviado junto com a prova (no upload) ou adicionado posteriormente.

## Fluxo de Processamento

```
PDF do Gabarito
    │
    ▼
┌──────────────────┐
│ 1. PDF Parser     │  → Extrai texto bruto do PDF do gabarito
│  (PyMuPDF)        │     → Todas as páginas concatenadas
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 2. Answer Mapper  │  → Identifica pares questão → resposta
│  (LLM + Regex)    │     → Strategy 1: Regex (primeira tentativa)
│                   │     → Strategy 2: LLM (fallback se regex falhar)
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 3. Linker         │  → Vincula respostas às questões no banco
│                   │     → Atualiza questions.correct_answer
│                   │     → Atualiza questions.is_answerable = True
│                   │     → Atualiza exam.has_answer_key = True
└──────────────────┘
```

## Etapa 1 — PDF Parser do Gabarito

- Abrir o PDF do gabarito com PyMuPDF.
- Extrair texto de todas as páginas e concatenar.
- O gabarito pode ter formatos variados: tabela, lista, grade, etc.

## Etapa 2 — Answer Mapper

### Strategy 1: Regex (Primeira Tentativa)

Padrões comuns de gabaritos:

```
# Formato 1: "Questão 1: A" ou "Questão 1 - A"
(?i)(questão|questao|quest[\.\s])\s*(\d+)\s*[:\-—]\s*([A-E])

# Formato 2: "01 - A" ou "01. A"
^\s*(\d+)\s*[\.\)\-—]\s*([A-E])

# Formato 3: Tabela "01 A 02 B 03 C"
(\d+)\s+([A-E])

# Formato 4: Certo/Errado
(?i)(questão|questao)\s*(\d+)\s*[:\-—]\s*(Certo|Errado|C|E)
```

- Tentar cada padrão sequencialmente.
- Se um padrão encontrar pelo menos 70% das questões esperadas, considerar sucesso.
- Se nenhum regex encontrar resultados satisfatórios, ir para Strategy 2.

### Strategy 2: LLM Fallback

- Enviar o texto bruto do gabarito ao LLM.
- Prompt: "Extraia o gabarito deste texto. Retorne um JSON com lista de objetos {question_number, correct_answer}. correct_answer deve ser A, B, C, D, E para múltipla escolha ou C (Certo) / E (Errado) para certo/errado."

### JSON Schema de Resposta do LLM

```json
{
  "type": "object",
  "required": ["answers"],
  "properties": {
    "answers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["question_number", "correct_answer"],
        "properties": {
          "question_number": {"type": "integer"},
          "correct_answer": {
            "type": "string",
            "enum": ["A", "B", "C", "D", "E"]
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

> **Nota:** Para questões do tipo `true_false`, `C` = Certo e `E` = Errado.

## Etapa 3 — Linker

### Responsabilidades
- Para cada par `{question_number, correct_answer}` extraído:
  - Buscar a questão no banco: `SELECT * FROM questions WHERE exam_id = ? AND question_number = ?`.
  - Se encontrada:
    - Atualizar `correct_answer = ?`.
    - Atualizar `is_answerable = True`.
  - Se não encontrada:
    - Logar warning: "Questão {n} não encontrada na prova {exam_id}."
    - Continuar (não abortar).
- Atualizar `exam.has_answer_key = True`.
- Atualizar `exam.answer_key_pdf_path` se ainda não estiver setado.

## Regras de Negócio

1. O gabarito só pode ser processado se a prova já tiver passado pela extração (`status = 'completed'`).
2. Se a prova estiver em `pending` ou `extracting`, o processamento do gabarito é enfileirado e aguarda a conclusão da extração.
3. O gabarito pode ser re-processado (se já processado antes) — atualiza os `correct_answer` existentes.
4. A resposta correta deve ser compatível com o tipo da questão:
   - `multiple_choice`: A, B, C, D, E.
   - `true_false`: C (Certo) ou E (Errado).
5. Se o gabarito contiver respostas para questões inexistentes na prova, essas entradas são ignoradas (logadas como warning).
6. Se o gabarito não contiver resposta para alguma questão existente, essa questão permanece com `is_answerable = False` e `correct_answer = NULL`.
7. O regex é tentado primeiro por ser mais rápido e não consumir tokens de IA.
8. O LLM é fallback — só usado se o regex não encontrar pelo menos 70% das respostas esperadas.
9. `exam.has_answer_key = True` só é setado após o processamento ser concluído com sucesso.

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-AK-01 | Extrair texto do PDF do gabarito com PyMuPDF                                |
| FR-AK-02 | Tentar padrões regex para mapear questão → resposta                         |
| FR-AK-03 | Se regex encontrar <70% das esperadas, usar LLM como fallback              |
| FR-AK-04 | Enviar texto do gabarito ao LLM com prompt estruturado                      |
| FR-AK-05 | Validar resposta do LLM contra JSON Schema                                  |
| FR-AK-06 | Vincular respostas às questões no banco (atualizar correct_answer)          |
| FR-AK-07 | Atualizar `is_answerable = True` para questões com resposta                |
| FR-AK-08 | Atualizar `exam.has_answer_key = True` ao concluir                          |
| FR-AK-09 | Permitir adicionar gabarito a prova existente                              |
| FR-AK-10 | Permitir re-processamento de gabarito                                       |
| FR-AK-11 | Logar warnings para questões não encontradas no banco                       |
| FR-AK-12 | Aguardar conclusão da extração se prova estiver em `extracting`            |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-AK-01 | Regex deve executar em < 1 segundo                                    |
| NFR-AK-02 | Timeout de chamada LLM: 60 segundos                                   |
| NFR-AK-03 | Máximo de 2 retries se LLM retornar JSON inválido                     |

## Casos de Erro

| ID    | Cenário                                               | Comportamento                                            |
|-------|-------------------------------------------------------|----------------------------------------------------------|
| ERR-AK-01 | PDF do gabarito corrompido                         | Mensagem: "PDF do gabarito inválido ou corrompido."      |
| ERR-AK-02 | Nenhum padrão regex encontrado e LLM também falha  | Mensagem: "Não foi possível extrair o gabarito."         |
| ERR-AK-03 | LLM retorna JSON inválido após 2 retries           | Fallback: usar o que regex encontrou (mesmo que parcial) |
| ERR-AK-04 | Resposta incompatível com tipo da questão          | Ignorar aquela resposta; logar warning                   |
| ERR-AK-05 | Gabarito com menos de 50% das respostas            | Avisar usuário: "Gabarito processado parcialmente."      |
| ERR-AK-06 | Prova em `extracting` ao tentar processar gabarito | Enfileirar; processar após extração concluir             |
| ERR-AK-07 | Prova em `error` ao tentar processar gabarito      | Mensagem: "Re-processe a prova antes de adicionar gabarito." |

## Critérios de Aceitação

1. O texto do PDF do gabarito é extraído com PyMuPDF.
2. Padrões regex tentam mapear questão → resposta.
3. Se regex encontra <70% das esperadas, o LLM é usado como fallback.
4. A resposta do LLM é validada contra o JSON Schema.
5. As respostas são vinculadas às questões no banco (`correct_answer` atualizado).
6. Questões com resposta têm `is_answerable = True`.
7. `exam.has_answer_key = True` após processamento concluído.
8. É possível adicionar gabarito a uma prova existente sem gabarito.
9. É possível re-processar o gabarito de uma prova.
10. Questões não encontradas no banco são logadas como warning (não abortam).
11. Respostas incompatíveis com o tipo da questão são ignoradas.
12. Se a prova está em `extracting`, o gabarito aguarda a extração concluir.

## Fora de Escopo

- Gabarito embutido no próprio PDF da prova (não separado) — suporte apenas para gabarito em PDF separado.
- Gabarito em formatos não-PDF (imagens, planilhas, texto).
- Validação cruzada entre gabarito e alternativas da questão (ex: se gabarito diz "F" mas questão não tem alternativa F).
