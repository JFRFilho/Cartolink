# 🔗 CartLink — Google Drive File Sharing

> Ferramenta corporativa para envio de arquivos ao Google Drive com geração automática de link público.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![Google Drive API](https://img.shields.io/badge/Google%20Drive-API%20v3-yellow)

---

## ✨ Funcionalidades

- 📂 Interface web moderna com drag-and-drop
- ☁️ Upload direto para o Google Drive via API oficial
- 🔓 Permissão pública automática (qualquer pessoa com o link)
- 🔗 Geração e cópia do link compartilhável
- 📊 Acompanhamento em tempo real do processo
- 📱 Design responsivo (desktop e mobile)
- 🕐 Histórico da última operação

---

## 📁 Estrutura do Projeto

```
cartlink/
├── app/
│   ├── __init__.py
│   ├── main.py           # Factory da aplicação Flask
│   ├── routes.py         # Endpoints HTTP
│   ├── drive_service.py  # Wrapper da API do Google Drive
│   └── auth.py           # Fluxo OAuth 2.0
├── templates/
│   └── index.html        # Interface principal
├── static/
│   ├── css/
│   │   └── styles.css    # Estilos customizados
│   └── js/
│       └── app.js        # Lógica do frontend
├── config/               # (criada automaticamente)
│   ├── credentials.json  # ← você vai colocar aqui
│   └── token.json        # ← gerado automaticamente
├── temp_uploads/         # (criada automaticamente)
├── run.py                # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Configuração Passo a Passo

### Pré-requisitos

- Python 3.10 ou superior
- Conta Google
- VS Code (recomendado)

---

### Passo 1 — Clonar e instalar dependências

```bash
# Entre na pasta do projeto
cd cartlink

# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

---

### Passo 2 — Configurar o Google Cloud Console

Esta é a etapa mais importante. Siga com atenção:

#### 2.1 — Criar um projeto no Google Cloud

1. Acesse [https://console.cloud.google.com](https://console.cloud.google.com)
2. Clique em **"Selecionar projeto"** → **"Novo projeto"**
3. Nome: `CartLink` → **Criar**
4. Certifique-se de que o novo projeto está selecionado

#### 2.2 — Ativar a Google Drive API

1. No menu lateral, vá em **"APIs e serviços"** → **"Biblioteca"**
2. Pesquise por `Google Drive API`
3. Clique em **"Google Drive API"** → **"Ativar"**

#### 2.3 — Configurar a Tela de Consentimento OAuth

1. Vá em **"APIs e serviços"** → **"Tela de consentimento OAuth"**
2. Selecione **"Externo"** → **Criar**
3. Preencha:
   - **Nome do app:** CartLink
   - **E-mail de suporte:** seu e-mail
   - **E-mail do desenvolvedor:** seu e-mail
4. Clique em **"Salvar e continuar"** nas próximas telas (Escopos e Usuários de teste)
5. Em **"Usuários de teste"**, adicione seu próprio e-mail do Google
6. Finalize

> ⚠️ **Importante:** Enquanto o app estiver em modo "Teste", apenas os e-mails na lista de usuários de teste poderão autenticar.

#### 2.4 — Criar credenciais OAuth 2.0

1. Vá em **"APIs e serviços"** → **"Credenciais"**
2. Clique em **"+ Criar credenciais"** → **"ID do cliente OAuth 2.0"**
3. Tipo de aplicativo: **"Aplicativo da Web"**
4. Nome: `CartLink Local`
5. Em **"URIs de redirecionamento autorizados"**, adicione:
   ```
   http://localhost:5000/auth/callback
   ```
6. Clique em **"Criar"**
7. Uma janela aparecerá com seu **Client ID** e **Client Secret**
8. Clique em **"Baixar JSON"**
9. Renomeie o arquivo baixado para `credentials.json`
10. Mova-o para a pasta `config/` do projeto

---

### Passo 3 — Configurar o arquivo .env

```bash
# Copie o arquivo de exemplo
cp .env.example .env
```

Edite o `.env` e ajuste conforme necessário:

```env
SECRET_KEY=uma-chave-secreta-aleatoria-aqui
FLASK_DEBUG=True
PORT=5000
OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback
MAX_FILE_SIZE_MB=100
```

Para gerar uma SECRET_KEY segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Passo 4 — Rodar no VS Code

#### Via terminal integrado do VS Code:

```bash
python run.py
```

#### Via configuração de launch (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "CartLink",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run.py",
      "env": {
        "FLASK_DEBUG": "true"
      },
      "jinja": true
    }
  ]
}
```

Pressione **F5** para iniciar com debug.

---

### Passo 5 — Autenticar com Google

1. Acesse [http://localhost:5000](http://localhost:5000)
2. Clique em **"Conectar com Google"**
3. Faça login com a conta Google adicionada como usuário de teste
4. Autorize o CartLink a gerenciar arquivos do Drive
5. Você será redirecionado de volta ao CartLink com o status **"Conectado ao Drive"**

> O token de autenticação é salvo em `config/token.json` e atualizado automaticamente quando expirar.

---

## 🧪 Testando o Sistema

1. Com o servidor rodando e autenticado, acesse `http://localhost:5000`
2. Arraste um arquivo para a área de upload (ou clique para selecionar)
3. Clique em **"Enviar para o Drive"**
4. Acompanhe o progresso em tempo real no painel de status
5. Copie o link gerado e teste em uma aba anônima

---

## 🔧 Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | *(obrigatório)* | Chave secreta do Flask |
| `FLASK_DEBUG` | `True` | Modo debug (desative em produção) |
| `PORT` | `5000` | Porta do servidor |
| `OAUTH_REDIRECT_URI` | `http://localhost:5000/auth/callback` | URI de callback OAuth |
| `GOOGLE_DRIVE_FOLDER_ID` | *(vazio)* | ID da pasta no Drive (opcional) |
| `MAX_FILE_SIZE_MB` | `100` | Limite de tamanho em MB |
| `ALLOWED_EXTENSIONS` | pdf,doc,docx,... | Extensões permitidas |

---

## 🔒 Segurança

- **Nunca commite** `credentials.json`, `token.json` ou `.env` no Git
- O arquivo `.gitignore` já os exclui por padrão
- Use `FLASK_DEBUG=False` em ambientes de produção
- Em produção, use HTTPS e um servidor WSGI (Gunicorn + Nginx)

---

## 📦 Dependências

| Pacote | Versão | Finalidade |
|---|---|---|
| Flask | 3.0.x | Framework web |
| flask-cors | 4.0.x | CORS headers |
| google-api-python-client | 2.x | Google Drive API |
| google-auth-oauthlib | 1.x | Fluxo OAuth 2.0 |
| python-dotenv | 1.x | Variáveis de ambiente |

---

## 🐛 Solução de Problemas

**Erro: `credentials.json not found`**
→ Baixe as credenciais no Google Cloud Console e coloque em `config/credentials.json`

**Erro: `redirect_uri_mismatch`**
→ Certifique-se que `http://localhost:5000/auth/callback` está na lista de URIs autorizados no Console

**Erro: `Access blocked: This app's request is invalid`**
→ Adicione seu e-mail como usuário de teste na tela de consentimento OAuth

**Upload falha com 401**
→ Clique em "Desconectar" e reconecte com o Google

---

## 📄 Licença

MIT — use livremente para projetos pessoais e corporativos.

---

*Desenvolvido com Flask, Google Drive API v3 e muito café ☕*
---

## Docker

O projeto agora pode ser executado em container com `Dockerfile` e `docker-compose.yml`.

### Subir localmente com Docker

```bash
cp .env.example .env

# ajuste sua .env
docker compose up --build -d
```

Abra no navegador em `http://localhost:5000`.

Se sua `.env` usar outra porta, o compose respeitara o valor de `PORT`.

### Ubuntu 24.04

Depois de clonar o projeto no servidor:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker

cd cartlink
cp .env.example .env
nano .env

docker compose up --build -d
docker compose logs -f
```

Para atualizar depois de um `git pull`:

```bash
docker compose up --build -d
```

Para parar:

```bash
docker compose down
```

### Observacoes importantes

- A imagem nao copia `.env`, `config/credentials.json` nem `config/token.json`.
- O container usa as credenciais via variaveis de ambiente, que e o fluxo mais seguro para deploy.
- O diretorio `temp_uploads/` fica montado como volume para uploads temporarios.
- A `OAUTH_REDIRECT_URI` da `.env` precisa bater exatamente com a URI cadastrada no Google Cloud para o ambiente Ubuntu.
