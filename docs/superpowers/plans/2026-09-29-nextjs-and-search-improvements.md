# Frontend Next.js & Melhorias na Busca Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o frontend web responsivo em Next.js com Tailwind CSS (paleta `#E7D6A3`, `#F9DF80`, `#352723`, `#B3965E`), aprimorar o algoritmo de busca determinística no backend Django Ninja para correspondência precisa de frases e adicionar endpoint de autocompletar com até 4 sugestões.

**Architecture:** O frontend Next.js 14+ se comunica via requisições assíncronas com o backend Django Ninja (`http://127.0.0.1:8000/api/v1`). O backend consulta o banco SQLite local (`db.sqlite3`) para realizar buscas ponderadas com exatidão de frase e sugerir termos conforme o usuário digita.

**Tech Stack:** Next.js 14+ (App Router, React, TypeScript), Tailwind CSS, Django 6.1, Django Ninja, SQLite3, Pytest.

**Spec:** `docs/superpowers/specs/2026-09-29-nextjs-and-search-improvements-design.md`

## Global Constraints
- Python 3.14 e Django >= 6.0
- Node.js e npm disponíveis no ambiente Windows
- Cores obrigatórias: Primária `#E7D6A3`, Secundária `#F9DF80`, Terciária `#352723`, Acentos `#B3965E`
- Mínimo de 2 palavras para pesquisa final; sugestões de autocomplete ativadas com 2+ caracteres
- Preservar arquivos e banco SQLite com dados já indexados

## Review Focus
1. Busca por frase *"nós vos damos graças"* não deve trazer falsos positivos com apenas uma palavra presente.
2. Múltiplos arquivos contendo o mesmo canto devem todos ser retornados e agrupados claramente.
3. Clique em "Abrir Localização" para arquivos do Google Drive deve abrir a URL do arquivo no navegador.
4. O menu de sugestões de autocompletar deve exibir até 4 itens com rolagem suave.
5. Frontend Next.js responsivo para mobile, tablet e desktop.

---

### Task 1: Aprimoramento da Busca Determinística e Resolução de Falsos Positivos

**Files:**
- Modify: `finder_files/services.py:220-290`
- Test: `tests/test_validation_and_search.py`

**Interfaces:**
- Consumes: `DocumentChunk`, `IndexedFile`
- Produces: `FileSearchService.search(query: str) -> List[Dict[str, Any]]` com correspondência estrita para termos significativos e super-bônus de frase.

- [ ] **Step 1: Escrever teste de regressão para frase específica**
No arquivo `tests/test_validation_and_search.py`, adicionar teste garantindo que frase como *"nós vos damos graças"* não retorne trecho contendo apenas *"nós vos louvamos"*.

- [ ] **Step 2: Executar teste para verificar falha inicial**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validation_and_search.py`
Expected: FAIL se houver falso positivo.

- [ ] **Step 3: Ajustar algoritmo de pontuação em `finder_files/services.py`**
Exigir presença de 100% dos termos significativos para buscas curtas (<=3 palavras) e adicionar bônus de 100 pontos para correspondência da frase inteira contígua.

- [ ] **Step 4: Executar testes para verificar aprovação**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validation_and_search.py`
Expected: PASS

---

### Task 2: Endpoint de Sugestões de Autocomplete na API

**Files:**
- Modify: `finder_files/services.py`
- Modify: `finder_files/api.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Produces: `GET /api/v1/search/suggestions?q={prefix}` -> `List[str]` (máximo 4 sugestões)

- [ ] **Step 1: Escrever teste para o endpoint de sugestões**
Adicionar teste em `tests/test_api.py` chamando `/api/v1/search/suggestions?q=San` e verificando formato de retorno.

- [ ] **Step 2: Executar teste para verificar ausência do endpoint**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api.py`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implementar método `get_suggestions` e rota Ninja API**
Em `finder_files/services.py`, implementar busca rápida de até 4 sugestões baseadas em títulos de arquivos e trechos iniciais de músicas. Registrar rota GET em `finder_files/api.py`.

- [ ] **Step 4: Executar testes para verificar aprovação**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_api.py`
Expected: PASS

---

### Task 3: Suporte a Links Diretos do Google Drive na Resposta da API

**Files:**
- Modify: `finder_files/services.py`
- Modify: `finder_files/api.py`
- Modify: `finder_files/gdrive_service.py`

**Interfaces:**
- Produces: campo `open_url: Optional[str]` em `SearchResultItem`

- [ ] **Step 1: Atualizar schema `SearchResultItem` em `finder_files/api.py`**
Adicionar campo `open_url: Optional[str] = None`.

- [ ] **Step 2: Popular `open_url` em `FileSearchService.search`**
Se `chunk.indexed_file.source == 'google_drive'`, extrair ID do arquivo ou link do cache e gerar URL pública para navegação direta (`https://docs.google.com/presentation/d/...` ou URL do Drive).

- [ ] **Step 3: Executar pytest para garantir conformidade**
Run: `.\.venv\Scripts\python.exe -m pytest`
Expected: PASS (9+ testes)

---

### Task 4: Criação do Projeto Frontend Next.js com Tailwind CSS

**Files:**
- Create: `frontend_next/package.json`
- Create: `frontend_next/tailwind.config.js`
- Create: `frontend_next/postcss.config.js`
- Create: `frontend_next/tsconfig.json`
- Create: `frontend_next/src/app/globals.css`
- Create: `frontend_next/src/app/layout.tsx`

**Interfaces:**
- Produces: Base do aplicativo Next.js configurada com a paleta `#E7D6A3`, `#F9DF80`, `#352723`, `#B3965E`.

- [ ] **Step 1: Inicializar estrutura do Next.js em `frontend_next/`**
Criar `package.json` com Next.js 14+, React 18+, Lucide React e Tailwind CSS.

- [ ] **Step 2: Configurar `tailwind.config.js` com a paleta exigida**
Definir cores `primary: '#E7D6A3'`, `secondary: '#F9DF80'`, `tertiary: '#352723'`, `accent: '#B3965E'`.

- [ ] **Step 3: Instalar dependências via npm**
Executar instalação em `frontend_next/`.

---

### Task 5: Componentes da Interface Web (Busca, Autocomplete e Resultados)

**Files:**
- Create: `frontend_next/src/components/Header.tsx`
- Create: `frontend_next/src/components/SearchBar.tsx`
- Create: `frontend_next/src/components/AutocompleteDropdown.tsx`
- Create: `frontend_next/src/components/ResultCard.tsx`
- Create: `frontend_next/src/components/SearchResultsList.tsx`
- Create: `frontend_next/src/app/page.tsx`

**Interfaces:**
- Consumes: `/api/v1/search`, `/api/v1/search/suggestions`

- [ ] **Step 1: Criar componente de cabeçalho (`Header.tsx`)**
Título elegante com visual sacro/dourado e indicador de status da API.

- [ ] **Step 2: Criar campo de busca com autocomplete (`SearchBar.tsx` e `AutocompleteDropdown.tsx`)**
Debounce de 200ms na digitação, exibição de até 4 sugestões com rolagem, navegação por teclado e submit com validação de 2 palavras.

- [ ] **Step 3: Criar componente de card e lista de resultados (`ResultCard.tsx` e `SearchResultsList.tsx`)**
Renderização de resultados com badges de origem (Local vs Google Drive), número do slide/página, trecho da música e botão "Abrir Localização" com suporte a link do navegador.

- [ ] **Step 4: Integrar na página principal `src/app/page.tsx`**
Gerenciamento de estado (consulta, resultados, carregamento, erros, filtros de origem).

---

### Task 6: Execução Simultânea e Verificação End-to-End

**Files:**
- Verify: `http://127.0.0.1:8000/api/v1/docs` (Django Ninja)
- Verify: `http://localhost:3000` (Next.js)

- [ ] **Step 1: Iniciar servidor backend Django**
Comando: `python manage.py runserver 8000` em segundo plano.

- [ ] **Step 2: Iniciar servidor frontend Next.js**
Comando: `npm run dev` em `frontend_next` em segundo plano.

- [ ] **Step 3: Testar busca real no navegador**
Verificar busca por *"Santo Santo"*, *"nós vos damos graças"* e testar autocomplete interativo.
