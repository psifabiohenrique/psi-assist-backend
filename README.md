# 🧠 Psi Assist Backend

## 📌 Descrição Geral
O **Psi Assist Backend** é uma aplicação desenvolvida em **Django** para **gerenciamento de prontuários psicológicos**, com foco em **automação via inteligência artificial**.  
O sistema possibilita que psicólogos gravem sessões de atendimento diretamente no navegador; esses áudios são enviados para a **API do Google Gemini**, que gera **registros automatizados de sessão** (prontuários).  

Além do registro automatizado, o sistema também permite gerenciamento de pacientes, prontuários e configuração personalizada para cada usuário.

---

## 🎯 Propósitos do Projeto
- 📑 Facilitar o **registro clínico** de sessões psicológicas.  
- ⏱️ **Economizar tempo** do profissional com prontuários.  
- 🎙️ Permitir **gravação integrada de áudio** pelo navegador.  
- 🤖 Usar **inteligência artificial** (Google Gemini) para criar prontuários automaticamente.  
- 🎨 Oferecer uma **interface moderna e prática** com **TailwindCSS** e **Font Awesome**.
- 🔒 Oferecer experiência de armazenamento local de informações confidenciais.

---

## 🛠️ Tecnologias Utilizadas

### 🔹 Backend
- **Django** → framework robusto para criação de aplicações web.  
- **Custom User Model** (com campos para API Key e System Prompt).  
- **Threads no Django** → processamento de áudio assíncrono (background).
- **pydub com ffmpeg** → compressão e divisão dos áudios para processamento com GEMINI

### 🔹 Frontend
- **TailwindCSS** → estilização moderna e responsiva.  
- **Font Awesome** → ícones intuitivos para ações.  

### 🔹 Integrações
- **Google Gemini (gemini-2.5-flash)** → geração de texto a partir de áudio.  
- **Recorder JS (implementação própria)** → gravação e envio de áudio pelo navegador.  

### 🔹 Infraestrutura
- **uv** → gerenciador de versão do Python e pacotes (no lugar de pip/venv), disponível no [site oficial](https://docs.astral.sh/uv/guides/install-python/).  
- **SQLite/PostgreSQL** → banco de dados para pacientes e registros.  
- **Executável Windows** → binário disponível no GitHub, pronto para rodar sem setup manual.
- **FFMPEG** → biblioteca para manipulação de áudio, disponível no [site oficial](https://www.ffmpeg.org/download.html).

---

## 📂 Estrutura do Projeto

### 🔸 Módulo `user`
- Modelo `CustomUser` (extends `AbstractUser`).  
- Campos:
  - `api_key` (para integração com Gemini).  
  - `system_prompt` (configuração personalizada).  

### 🔸 Módulo `patients`
- CRUD completo de pacientes.  
- Relacionamento direto com usuários e múltiplos prontuários.  

### 🔸 Módulo `psy_records`
- Registro incremental de sessões.  
- Geração automática de prontuários via áudio + IA.  
- Thread em background para não travar a interface.  

### 🔸 Gravação de Áudio
- Implementado em **JavaScript modular**.  
- Feedback visual, botões de gravação, parada, cancelamento e opção de download local.  

---

## 🚀 Instalação e Configuração

### 🔹 Opção 1: Executável Windows (mais fácil)
- Baixe o `.exe` na área de **Releases**.  
- Execute o programa diretamente, sem precisar instalar dependências.  
- Na **primeira execução**, o banco de dados será criado **automaticamente**.  

### 🔹 Opção 2: Clonando Repositório (desenvolvedores)

1. **Instale o [uv](https://github.com/astral-sh/uv)** caso ainda não tenha:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh # Linux/mac
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" # Windows
   ```
   No windows, é possível que necessite alterar as políticas de execução!

2. **Instale o [FFMPEG](https://www.ffmpeg.org/download.html)** caso ainda não tenha:
   ```bash
   sudo apt install ffmpeg # Linux(Ubuntu)
   winget install ffmpeg # Windows
   ```
   No Mac, é possível encontrar o instalador no [site oficial](https://www.ffmpeg.org/download.html)

2. **Clone o repositório**
   ```bash
   git clone https://github.com/psifabiohenrique/psi-assist-backend.git
   cd psi_assist_backend
   ```

3. **Crie o ambiente virtual e Instale dependências**
   ```bash
   uv sync
   ```

4. **Rodar migrações**
   ```bash
   uv run python manage.py migrate
   ```

5. **Rodar servidor**
   ```bash
   uv run python manage.py runserver
   ```

---

## 🔮 Próximos Passos
- [ ] Implementar auxílio de acompanhamento psicológico.
- [ ] Desenvolver sistema automatizado de relatórios.
- [ ] Dashboard com estatísticas dos atendimentos.  
- [ ] Exportação de prontuários (PDF, DOCX).  
- [ ] Implementação de permissões para equipes de psicólogos.  
- [ ] Integração com agenda/calendário.  

---

## 👨‍💻 Autor
**Fábio Henrique** - psifabiohenrique@outlook.com
Projeto desenvolvido no contexto de inovação em **atendimento psicológico com IA**.