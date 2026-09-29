# 🎵 Buscador de Músicas (`arquivos_missa`)

Aplicação Desktop profissional para localização rápida, precisa e confiável de músicas, letras e apresentações em arquivos do computador (.ppt, .pptx, .doc, .docx, .pdf) e do Google Drive.

---

## 🚀 Como Executar o Projeto

### 1. Criar e Ativar Ambiente Virtual (Python 3.14)
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\activate
```

### 2. Instalar Dependências
```powershell
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente (.env)
Copie o arquivo de exemplo `.env.example` para `.env`:
```powershell
copy .env.example .env
```

### 4. Executar Migrações do Banco de Dados
```powershell
python manage.py migrate
```

### 5. Executar a Aplicação Desktop (CustomTkinter)
```powershell
python frontend_ctk/app.py
```

### 6. Executar o Servidor de API (Django Ninja)
```powershell
python manage.py runserver 8000
```

---

## 🧪 Execução de Testes
Para rodar a suíte completa de testes automatizados:
```powershell
pytest
```

---

## 📦 Empacotamento para Windows (Gerar .EXE)
Para compilar a aplicação em um executável (.exe) independente para Windows:
```powershell
python build_exe.py
```
O arquivo final estará disponível em: `dist/BuscadorDeMusicas.exe`.

---

## 📑 Suporte a Formatos de Documento
- **Presentações (.ppt, .pptx):** Identifica e preserva o número exato do **Slide**.
- **Documentos PDF (.pdf):** Identifica e preserva o número exato da **Página**.
- **Documentos Word (.doc, .docx):** Identifica seções e parágrafos.
- **Google Drive:** Baixa e sincroniza automaticamente arquivos de pastas compartilhadas do Drive.
