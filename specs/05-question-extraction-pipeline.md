# Spec 05 — Pipeline Híbrido de Extração de Questões

## Objetivo

Definir o pipeline de extração de questões a partir de PDFs de provas, combinando parsing de texto, identificação/recorte de elementos visuais e estruturação via LLM com JSON Schema rígido.

## Contexto

O pipeline é o coração da aplicação. Ele transforma um PDF de prova não-estruturado em questões estruturadas no banco de dados. O pipeline é híbrido porque combina extração de texto (determinística) com inteligência artificial (LLM) para estruturação semântica.

## Arquitetura do Pipeline

```
PDF da Prova
    │
    ▼
┌──────────────┐
│  1. PDF Parser │  → Extrai texto bruto + metadados de páginas
│  (PyMuPDF)     │     → Identifica blocos de texto, posições (bbox)
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ 2. Image Extractor│  → Identifica elementos não-textuais
│  (Pillow/OpenCV)  │     → Recorta imagens: gráficos, tabelas, fórmulas
│                   │     → Salva em /data/assets/{workspace_id}/{question_id}_{idx}.png
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 3. LLM Extractor  │  → Estrutura questões via LLM
│  (AI Adapter)     │     → Input: texto + referências de imagem
│                   │     → Output: JSON Schema rígido
│                   │     → Identifica: número, enunciado, alternativas, tópico
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 4. Persistence    │  → Salva questões no SQLite
│                   │     → Atualiza exam.status = 'completed'
│                   │     → Atualiza exam.question_count
└──────────────────┘
```

## Etapa 1 — PDF Parser (PyMuPDF / pdfplumber)

### Responsabilidades
- Abrir o PDF com PyMuPDF (`fitz`).
- Iterar sobre cada página.
- Extrair texto bruto com posições (bounding boxes).
- Identificar quebras de questão (padrões como "Questão 1", "01.", "1 -", etc.).
- Agrupar texto em blocos que representam potenciais questões.
- Identificar regiões da página que contêm elementos não-textuais (imagens embutidas, vetores, tabelas).

### Padrões de Identificação de Questão
- Regex: `(?i)(questão|questao|quest[\.\s])\s*(\d+)`
- Regex: `^\d+[\.\)\-]\s` (número no início de linha)
- Regex: `^\d+\s*[-–—]\s` (número com travessão)

### Output da Etapa 1
```python
{
  "pages": [
    {
      "page_number": 1,
      "text": "...",
      "blocks": [
        {
          "question_number": 1,
          "raw_text": "enunciado + alternativas...",
          "bbox": [x0, y0, x1, y1],
          "image_regions": [[x0, y0, x1, y1], ...]
        }
      ]
    }
  ]
}
```

## Etapa 2 — Image Extractor (Pillow / OpenCV)

### Responsabilidades
- Para cada `image_region` identificada na Etapa 1:
  - Recortar a região do PDF renderizado em alta resolução (DPI 200+).
  - Salvar como PNG em `/data/assets/{workspace_id}/{question_id}_{index}.png`.
  - Registrar o caminho relativo na lista `image_paths` da questão.
- Identificar tipos de elemento visual:
  - Gráficos (linha, barra, pizza)
  - Tabelas
  - Fórmulas matemáticas
  - Diagramas/esquemas
  - Mapas

### Regras
- Renderizar a página em DPI 200 para qualidade de recorte.
- Se nenhuma imagem for encontrada para uma questão, `image_paths` fica vazio (não é erro).
- O formato de saída é sempre PNG.
- Nomes de arquivo: `{question_id}_{index}.png` (ex: `42_0.png`, `42_1.png`).

## Etapa 3 — LLM Extractor (AI Adapter)

### Responsabilidades
- Para cada bloco de texto bruto (potencial questão):
  - Montar prompt com o texto extraído + referências de imagens recortadas.
  - Enviar ao LLM via adapter do provedor configurado.
  - Receber resposta estruturada em JSON.
  - Validar a resposta contra o JSON Schema.

### Prompt Strategy
- **System prompt:** "Você é um especialista em extrair questões de provas. Extraia a estrutura completa da questão a partir do texto fornecido. Retorne APENAS JSON válido conforme o schema."
- **User prompt:** Inclui o texto bruto da questão e referências às imagens recortadas (descrição do que foi recortado, não a imagem em si a menos que o provedor suporte visão).

### JSON Schema de Resposta do LLM

```json
{
  "type": "object",
  "required": ["question_number", "statement", "question_type", "options", "topic_primary"],
  "properties": {
    "question_number": {
      "type": "integer",
      "description": "Número da questão na prova"
    },
    "statement": {
      "type": "string",
      "description": "Enunciado completo da questão"
    },
    "question_type": {
      "type": "string",
      "enum": ["multiple_choice", "true_false"],
      "description": "Tipo da questão"
    },
    "options": {
      "type": "object",
      "description": "Alternativas da questão. Para multiple_choice: {\"A\": \"...\", \"B\": \"...\", ...}. Para true_false: {\"C\": \"Certo\", \"E\": \"Errado\"}.",
      "minProperties": 2
    },
    "topic_primary": {
      "type": "string",
      "description": "Tópico/matéria principal da questão"
    },
    "topic_secondary": {
      "type": "string",
      "description": "Tópico secundário (opcional)"
    },
    "has_image_references": {
      "type": "boolean",
      "description": "Se a questão contém referências a imagens/gráficos"
    },
    "image_descriptions": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Descrições dos elementos visuais identificados"
    }
  },
  "additionalProperties": false
}
```

### Validação da Resposta
1. O JSON retornado deve ser válido (parseável).
2. Deve conter todos os campos `required`.
3. `question_type` deve ser `multiple_choice` ou `true_false`.
4. `options` deve ter no mínimo 2 entradas.
5. Para `multiple_choice`, as chaves devem ser letras (A, B, C, D, E).
6. Para `true_false`, as chaves devem ser C (Certo) e E (Errado).
7. Se a validação falhar, tentar novamente (máximo 2 retries).

## Etapa 4 — Persistence

### Responsabilidades
- Para cada questão extraída e validada:
  - Criar registro em `questions` com os campos mapeados.
  - `image_paths` = lista de caminhos relativos das imagens salvas.
  - `is_answerable` = `False` (gabarito é processado separadamente).
  - `correct_answer` = `NULL`.
- Atualizar `exam.status = 'completed'`.
- Atualizar `exam.question_count` = número de questões extraídas.
- Em caso de erro, atualizar `exam.status = 'error'`.

## Regras de Negócio

1. O pipeline é executado em background (threading) para não bloquear a UI.
2. O status da prova é atualizado para `extracting` no início e `completed`/`error` no fim.
3. Se o LLM falhar para uma questão específica, a questão é pulada e logada — o pipeline continua.
4. Se mais de 50% das questões falharem, o status da prova é `error` (não `completed`).
5. Não há extração de resposta correta nesta etapa — isso é responsabilidade do gabarito (Spec 06).
6. Questões extraídas sem gabarito têm `is_answerable = False`.
7. Re-processamento: se uma prova em `error` for re-processada, as questões anteriormente extraídas são deletadas antes de re-extrair.
8. O pipeline suporta PDFs com texto extraível. PDFs puramente digitalizados (sem texto) requerem OCR adicional — fora de escopo inicial.

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-PL-01 | Abrir PDF com PyMuPDF e extrair texto por página                            |
| FR-PL-02 | Identificar blocos de questão via regex padrões                             |
| FR-PL-03 | Identificar regiões de imagens não-textuais no PDF                          |
| FR-PL-04 | Recortar imagens em alta resolução (DPI 200) e salvar como PNG             |
| FR-PL-05 | Salvar imagens em `/data/assets/{workspace_id}/{question_id}_{idx}.png`   |
| FR-PL-06 | Enviar blocos de texto ao LLM com prompt estruturado                        |
| FR-PL-07 | Receber e validar resposta do LLM contra JSON Schema                        |
| FR-PL-08 | Persistir questões no banco com `is_answerable = False`                     |
| FR-PL-09 | Atualizar `exam.status` e `exam.question_count` ao final                   |
| FR-PL-10 | Permitir re-processamento de provas em status `error`                      |
| FR-PL-11 | Executar pipeline em background (threading)                                 |
| FR-PL-12 | Logar questões individuais que falharam sem abortar o pipeline             |
| FR-PL-13 | Deletar questões anteriores antes de re-processar                          |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-PL-01 | Renderização de páginas em DPI 200 para qualidade de recorte            |
| NFR-PL-02 | Timeout de chamada LLM: 60 segundos por questão                        |
| NFR-PL-03 | Máximo de 2 retries por questão em caso de falha de validação          |
| NFR-PL-04 | Pipeline executa em thread separada da UI                               |

## Casos de Erro

| ID    | Cenário                                             | Comportamento                                           |
|-------|-----------------------------------------------------|---------------------------------------------------------|
| ERR-PL-01 | PDF sem texto extraível (digitalizado)           | Status = `error`; mensagem: "PDF sem texto extraível."  |
| ERR-PL-02 | LLM retorna JSON inválido após 2 retries         | Questão é pulada; logada; pipeline continua             |
| ERR-PL-03 | LLM retorna schema válido mas com campos faltando | Questão é pulada; logada; pipeline continua             |
| ERR-PL-04 | Timeout na chamada LLM (60s)                    | Questão é pulada; pipeline continua                     |
| ERR-PL-05 | Falha ao salvar imagem recortada                 | Logar warning; questão ainda é persistida sem a imagem  |
| ERR-PL-06 | >50% das questões falham                        | Status da prova = `error`                               |
| ERR-PL-07 | API Key inválida durante extração               | Status = `error`; mensagem específica de auth           |
| ERR-PL-08 | Rate limit da API de IA                         | Backoff exponencial; se persistir, status = `error`     |

## Critérios de Aceitação

1. O pipeline extrai texto de PDFs usando PyMuPDF.
2. Padrões de regex identificam blocos de questão (número, enunciado, alternativas).
3. Regiões de imagens são identificadas e recortadas em DPI 200.
4. Imagens são salvas como PNG em `/data/assets/{workspace_id}/{question_id}_{idx}.png`.
5. O LLM recebe o texto e retorna JSON estruturado.
6. A resposta do LLM é validada contra o JSON Schema definido.
7. Questões válidas são persistidas no banco com `is_answerable = False`.
8. `exam.status` é atualizado para `completed` ao fim ou `error` em caso de falha crítica.
9. `exam.question_count` reflete o número de questões extraídas.
10. O pipeline roda em background sem bloquear a UI.
11. Falhas em questões individuais não abortam o pipeline.
12. Provas em `error` podem ser re-processadas (questões antigas são deletadas).
13. Se >50% das questões falham, o status é `error`.

## Fora de Escopo

- OCR de PDFs digitalizados como imagem (Tesseract) — futura melhoria.
- Envio de imagens diretamente ao LLM multimodal (visão) — futura melhoria quando provedor suportar.
- Extração de fórmulas LaTeX — apenas recorte de imagem da fórmula.
- Processamento paralelo de múltiplas questões no LLM (batch de prompts) — sequencial no escopo inicial.
