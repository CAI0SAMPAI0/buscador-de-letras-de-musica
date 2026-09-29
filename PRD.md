# Product Requirement Document (PRD) — Buscador de Músicas

## 1. Visão Geral e Objetivo
O **Buscador de Músicas** (`arquivos_missa`) é uma aplicação de alta velocidade e confiabilidade projetada para localizar músicas, letras e trechos textuais armazenados em apresentações (.ppt, .pptx), documentos de texto (.doc, .docx) e arquivos PDF (.pdf).

O sistema pesquisa tanto em diretórios locais do computador (HD/SSD, pendrives) quanto em pastas compartilhadas do Google Drive.

## 2. Requisitos Funcionais
- **Validação de Consulta:** Exige no mínimo 3 palavras para acionar a busca.
- **Indexação Incremental:** Varre arquivos e extrai trechos com hashing MD5 para evitar re-processamento.
- **Preservação de Localização:**
  - Apresentações (.ppt, .pptx): Preserva o número exato do slide (1-indexed).
  - PDFs (.pdf): Preserva o número da página (1-indexed).
  - Documentos Word (.doc, .docx): Preserva seções / parágrafos lógicos.
- **Busca Híbrida & Ranqueamento:** Combina busca lexical determinística (normalização ASCII, case-insensitive, pontuação por palavras encontradas) com ranking semântico contextual opcional assistido por LLM Meta Llama.
- **Integração Google Drive:** Sincronização e cache inteligente local de arquivos armazenados no Drive.
- **Interface Desktop:** Construída em CustomTkinter com tema escuro moderno, detalhes em azul e feedback visual assíncrono.

## 3. Requisitos Não-Funcionais
- **Linguagem & Framework:** Python 3.14 + Django 6.1.1 + Django Ninja (API assíncrona).
- **Interface Gráfica:** CustomTkinter 6.0.0.
- **Desempenho:** Resposta em tempo < 100ms para consultas no índice local.
- **Plataforma Alvo:** Windows 10/11 (empacotável via PyInstaller em executável `.exe` independente).

## 4. Arquitetura do Sistema
```
projeto/
├── core/                   # Configurações Django (base, dev, prod, urls, asgi)
├── finder_files/           # Modelos, extractors, serviços de indexação/busca e API Ninja
│   └── extractors/         # Extratores dedicados para PDF, PPTX, PPT, DOCX, DOC
├── ai/                     # Gerenciador de prompts em Markdown, provedores LLM (Meta Llama/Novita)
├── frontend_ctk/           # Interface Desktop CustomTkinter
├── tests/                  # Suíte de testes com Pytest e TestAsyncClient
└── dist/                   # Artefato executável Windows (.exe)
```

## 5. Decisões Arquiteturais Relevantes
1. **Busca Determinística como Fonte de Verdade:** A localização física de slides e páginas baseia-se estritamente nos dados extraídos e indexados no banco SQLite local. A IA é utilizada estritamente para expansão de consulta e re-ranqueamento semântico, impedindo alucinações.
2. **Prompts Desacoplados:** Prompts de IA estão armazenados em arquivos `.md` na pasta `ai/prompts/` e carregados via `PromptManager` com substituição segura de variáveis.
3. **UX Não-Bloqueante:** Requisições de rede e buscas longas rodam em threads de segundo plano no CustomTkinter.
