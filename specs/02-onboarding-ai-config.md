# Spec 02 — Onboarding & Configuração de IA

## Objetivo

Definir o fluxo de onboarding interativo para primeiro acesso e a configuração de provedores de IA, incluindo armazenamento seguro de credenciais.

## Contexto

No primeiro acesso, o usuário precisa ser guiado sobre como a aplicação funciona e deve configurar seu provedor de IA antes de poder usar as funcionalidades de extração. O onboarding é obrigatório e só ocorre uma vez.

## Fluxo de Onboarding (Passo a Passo)

### Passo 1 — Boas-vindas
- Tela de boas-vindas com logo e nome da aplicação.
- Texto explicativo: "Organize e pratique questões de provas em PDF com ajuda de IA."
- Botão "Começar".

### Passo 2 — Como funciona (Visão Gável)
- Explicação visual em 4 cards/etapas:
  1. **Crie um Workspace** — Organize suas provas por concurso/exame.
  2. **Faça upload de PDFs** — Envie provas e gabaritos.
  3. **Extração automática** — A IA extrai questões, alternativas, imagens e tópicos.
  4. **Pratique** — Responda questões, receba feedback e acompanhe seu desempenho.
- Botão "Próximo".

### Passo 3 — Escolha do Provedor de IA
- Apresentação dos 4 provedores suportados em cards selecionáveis:
  - **OpenAI** — Modelos: gpt-4o, gpt-4o-mini. Requer API Key.
  - **Google Gemini** — Modelos: gemini-1.5-pro, gemini-1.5-flash. Requer API Key.
  - **Anthropic Claude** — Modelos: claude-3.5-sonnet, claude-3-haiku. Requer API Key.
  - **Ollama (Local)** — Modelos: disponíveis no endpoint local. Requer URL do endpoint (ex: `http://localhost:11434`).
- Após seleção, exibir campos dinâmicos conforme o provedor.

### Passo 4 — Configuração de Credenciais
- **Para OpenAI / Gemini / Claude:**
  - Campo: `API Key` (input type=password, com botão toggle de visibilidade).
  - Campo: `Modelo` (dropdown com modelos disponíveis do provedor).
  - Botão "Testar Conexão" — envia uma chamada simples de validação.
- **Para Ollama:**
  - Campo: `URL do Endpoint` (ex: `http://localhost:11434`).
  - Campo: `Modelo` (dropdown populado dinamicamente via API `/api/tags` do Ollama).
  - Botão "Testar Conexão" — faz GET no endpoint para validar disponibilidade.

### Passo 5 — Confirmação e Conclusão
- Resumo das configurações escolhidas.
- Botão "Finalizar" → salva `onboarding_completed = "true"` em `settings`.
- Redireciona para a tela principal (lista de workspaces).

## Regras de Negócio

1. O onboarding só é exibido se `settings.onboarding_completed` for `false` ou inexistente.
2. O usuário não pode pular o onboarding — todos os passos devem ser completados.
3. A configuração de IA é obrigatória no onboarding — não é possível finalizar sem um provedor configurado e testado.
4. O botão "Testar Conexão" deve retornar sucesso antes de permitir avançar do Passo 4.
5. As credenciais (API Keys) devem ser armazenadas via `keyring` do SO (preferencial). Se `keyring` não estiver disponível, armazenar cifrado na tabela `settings` com `is_encrypted=True`.
6. O provedor de IA pode ser alterado posteriormente na tela de Configurações.
7. O campo `ai_provider`, `ai_model` e `ai_endpoint` são salvos em `settings` (não sensível).
8. O campo `ai_api_key` é salvo em `keyring` ou em `settings` com cifragem.

## Requisitos Funcionais

| ID     | Requisito                                                                    |
|--------|------------------------------------------------------------------------------|
| FR-OB-01 | Detectar primeiro acesso via consulta a `settings.onboarding_completed`    |
| FR-OB-02 | Exibir wizard de onboarding com 5 passos sequenciais                        |
| FR-OB-03 | Apresentar 4 provedores de IA em cards selecionáveis                        |
| FR-OB-04 | Exibir campos dinâmicos conforme provedor selecionado                       |
| FR-OB-05 | Validar API Key / Endpoint via botão "Testar Conexão"                       |
| FR-OB-06 | Persistir configurações de IA em `settings` e `keyring`                    |
| FR-OB-07 | Marcar `onboarding_completed = "true"` ao finalizar                         |
| FR-OB-08 | Redirecionar para tela principal após conclusão                             |
| FR-OB-09 | Permitir alteração de provedor/credenciais na tela de Configurações        |
| FR-OB-10 | Para Ollama, listar modelos disponíveis via GET `{endpoint}/api/tags`      |

## Requisitos Não Funcionais

| ID     | Requisito                                                                  |
|--------|----------------------------------------------------------------------------|
| NFR-OB-01 | O "Testar Conexão" deve ter timeout de 10 segundos                      |
| NFR-OB-02 | API Keys nunca devem ser exibidas em texto plano após input (mascarar)  |
| NFR-OB-03 | Transições entre passos devem ter feedback visual (animação/transição)  |

## JSON Schema — Validação de Configuração de IA

```json
{
  "provider": "openai | gemini | claude | ollama",
  "api_key": "string (requerido para openai/gemini/claude)",
  "endpoint": "string (requerido para ollama)",
  "model": "string (requerido)"
}
```

## Casos de Erro

| ID    | Cenário                                          | Comportamento                                           |
|-------|--------------------------------------------------|---------------------------------------------------------|
| ERR-OB-01 | API Key inválida ou expirada                  | Mensagem: "API Key inválida. Verifique e tente novamente." |
| ERR-OB-02 | Endpoint do Ollama inacessível                | Mensagem: "Não foi possível conectar ao Ollama. Verifique se está rodando." |
| ERR-OB-03 | Falha ao salvar credencial no keyring         | Fallback para tabela `settings` com cifragem; logar warning |
| ERR-OB-04 | Timeout no teste de conexão (10s)             | Mensagem: "Tempo limite excedido. Tente novamente."     |
| ERR-OB-05 | Modelo selecionado não suportado pelo provedor | Mensagem: "Modelo não disponível para este provedor."   |

## Critérios de Aceitação

1. Ao abrir a aplicação pela primeira vez (sem `onboarding_completed`), o wizard de onboarding é exibido.
2. O usuário pode navegar entre os 4 provedores e selecionar um.
3. Campos dinâmicos aparecem conforme o provedor (API Key para cloud, Endpoint para Ollama).
4. O botão "Testar Conexão" valida a configuração antes de permitir avançar.
5. Após finalizar, `settings.onboarding_completed = "true"` está persistido.
6. Ao reabrir a aplicação, o onboarding não é exibido novamente.
7. API Keys são armazenadas via `keyring` ou cifradas em `settings`.
8. Na tela de Configurações, o usuário pode trocar de provedor e re-testar conexão.
9. Para Ollama, os modelos são listados dinamicamente do endpoint.

## Fora de Escopo

- Onboarding com vídeo ou tutorial interativo animado.
- Suporte a mais de 4 provedores de IA no onboarding inicial.
- Configuração de múltiplas API Keys simultâneas (um provedor ativo por vez).
