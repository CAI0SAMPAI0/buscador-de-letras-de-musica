# Ranqueamento Semântico de Resultados

**Objetivo:** Reordenar candidatos a trechos de músicas com base na intenção da busca.
**Versão:** 1.0.0
**Contexto de Utilização:** Aplicado sobre os N melhores candidatos recuperados pelo banco de dados.
**Variáveis Esperadas:** {query}, {candidates_json}

## Instruções
Dada a consulta do usuário: "{query}"
E os seguintes trechos de documentos candidatos:
{candidates_json}

Avalie a relevância semântica de cada trecho para a música buscada e reordene por relevância.

## Critérios de Saída
Retorne uma lista JSON dos IDs dos candidatos reordenados do mais relevante para o menos relevante.
