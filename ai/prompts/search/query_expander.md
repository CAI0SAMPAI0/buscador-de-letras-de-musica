# Expansão e Normalização de Consulta

**Objetivo:** Normalizar termos de busca digitados pelo usuário, corrigindo erros de digitação e gerando variações para recuperação.
**Versão:** 1.0.0
**Contexto de Utilização:** Chamado quando a busca lexical determinística retorna poucos resultados.
**Variáveis Esperadas:** {user_query}

## Instruções
Analise a seguinte busca de música informada pelo usuário:
"{user_query}"

Identifique:
1. O termo normalizado (sem acentos e em minúsculas).
2. Sinônimos ou variações comuns da letra/título.
3. Palavras-chave essenciais para busca.

## Critérios de Saída
Retorne apenas um objeto JSON com as chaves:
- `normalized_query`: string
- `keywords`: lista de strings
- `variations`: lista de strings
