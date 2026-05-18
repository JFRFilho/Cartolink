# CartoLink 2.0

CartoLink 2.0 e uma aplicacao web em Flask para receber arquivos pelo navegador, enviar esses arquivos para uma conta fixa do Google Drive e gerar automaticamente um link publico de compartilhamento.

O objetivo do projeto e simples: o usuario final nao precisa fazer login no Google. O backend usa uma conta Google previamente autorizada, faz o upload via Google Drive API v3, aplica permissao publica no arquivo e devolve o link pronto para copiar.

## Funcionalidades

- Interface web responsiva para selecionar ou arrastar arquivos.
- Upload para o Google Drive usando a API oficial.
- Autenticacao OAuth 2.0 da conta Google usada pelo servidor.
- Geracao automatica de link publico.
- Acompanhamento de status do upload por polling.
- Validacao de extensoes permitidas e limite maximo de tamanho.
- Suporte a pasta especifica do Drive via `GOOGLE_DRIVE_FOLDER_ID`.
- Execucao local com Python ou em container Docker.

## Tecnologias

- Python 3.10+
- Flask 3
- Flask-CORS
- Google Drive API v3
- Google OAuth 2.0
- python-dotenv
- Gunicorn para execucao em container/producao

## Como Funciona

1. O administrador configura o projeto no Google Cloud e cria credenciais OAuth.
2. O administrador inicia o CartoLink 2.0 e acessa `/auth/google`.
3. O Google redireciona para `/auth/callback` com um codigo OAuth.
4. O backend troca o codigo por tokens e salva as credenciais.
5. A tela principal passa a aceitar uploads.
6. Cada arquivo enviado e salvo temporariamente em `temp_uploads/`.
7. Uma thread em segundo plano envia o arquivo ao Drive.
8. O backend torna o arquivo publico e retorna um link de visualizacao.
9. O arquivo temporario local e removido ao final do processo.

## Estrutura do Projeto

```text
cartlink/
|-- app/
|   |-- __init__.py
|   |-- main.py           # Factory da aplicacao Flask
|   |-- routes.py         # Rotas web, autenticacao e API de upload
|   |-- drive_service.py  # Integracao com Google Drive API
|   `-- auth.py           # Fluxo OAuth 2.0 e persistencia de token
|-- config/
|   |-- README.txt        # Orientacoes para arquivos sensiveis
|   |-- credentials.json  # Credenciais OAuth baixadas do Google Cloud, nao versionar
|   `-- token.json        # Token OAuth gerado apos autenticacao, nao versionar
|-- static/
|   |-- css/
|   |-- images/
|   `-- js/
|-- templates/
|   `-- index.html        # Interface principal
|-- temp_uploads/         # Arquivos temporarios de upload, nao versionar
|-- .env.example          # Modelo de configuracao
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- run.py
`-- README.md
```

## Rotas Principais

| Rota | Metodo | Descricao |
|---|---:|---|
| `/` | GET | Tela principal de upload |
| `/auth/google` | GET | Inicia a autorizacao OAuth da conta Google |
| `/auth/callback` | GET | Callback OAuth configurado no Google Cloud |
| `/auth/status` | GET | Retorna se o Drive esta autenticado |
| `/auth/logout` | GET | Remove o token local quando permitido |
| `/api/upload` | POST | Recebe o arquivo e inicia o upload para o Drive |
| `/api/status/<upload_id>` | GET | Consulta o status de um upload |

As rotas de autenticacao exigem acesso administrativo. Em modo local (`LOCAL_GOOGLE_TEST_MODE=True`) o acesso por `localhost` e liberado. Fora do modo local, use `ADMIN_SETUP_KEY` como query string `?key=...` ou no header `X-Admin-Setup-Key`.

## Pre-requisitos

- Python 3.10 ou superior.
- Conta Google.
- Projeto no Google Cloud com a Google Drive API ativada.
- Credenciais OAuth 2.0 do tipo "Aplicativo da Web".
- Docker e Docker Compose, caso queira rodar em container.

## Configuracao no Google Cloud

1. Acesse `https://console.cloud.google.com`.
2. Crie ou selecione um projeto.
3. Ative a `Google Drive API` em `APIs e servicos > Biblioteca`.
4. Configure a tela de consentimento OAuth.
5. Enquanto o app estiver em modo de teste, adicione seu e-mail em `Usuarios de teste`.
6. Crie uma credencial OAuth em `APIs e servicos > Credenciais`.
7. Escolha o tipo `Aplicativo da Web`.
8. Adicione a URI de callback autorizada.

Para desenvolvimento local, a URI normalmente e:

```text
http://localhost:5000/auth/callback
```

Se voce usar outra porta, por exemplo `5001`, cadastre exatamente:

```text
http://localhost:5001/auth/callback
```

Em deploy com dominio, cadastre a URL final com HTTPS:

```text
https://seudominio.com/auth/callback
```

Depois de criar a credencial, voce pode preencher `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no `.env` ou baixar o JSON, renomear para `credentials.json` e colocar em `config/credentials.json`.

## Instalacao Local

No Windows:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

No macOS ou Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Depois, edite o `.env` com seus valores.

## Variaveis de Ambiente

| Variavel | Exemplo | Descricao |
|---|---|---|
| `SECRET_KEY` | `change-this` | Chave secreta do Flask |
| `FLASK_DEBUG` | `True` | Liga ou desliga debug local |
| `PORT` | `5000` | Porta usada pelo Flask/Gunicorn |
| `LOCAL_GOOGLE_TEST_MODE` | `True` | Facilita o OAuth local e salva token em arquivo |
| `ADMIN_SETUP_KEY` | `change-this` | Chave para proteger rotas administrativas fora do localhost |
| `OAUTH_REDIRECT_URI` | `http://localhost:5000/auth/callback` | Callback OAuth, deve bater com o Google Cloud |
| `GOOGLE_CLIENT_ID` | `...apps.googleusercontent.com` | Client ID OAuth |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | Client Secret OAuth |
| `GOOGLE_PROJECT_ID` | `cartlink` | ID do projeto Google Cloud |
| `GOOGLE_AUTH_URI` | `https://accounts.google.com/o/oauth2/auth` | Endpoint de autorizacao Google |
| `GOOGLE_TOKEN_URI` | `https://oauth2.googleapis.com/token` | Endpoint de token Google |
| `GOOGLE_AUTH_PROVIDER_X509_CERT_URL` | `https://www.googleapis.com/oauth2/v1/certs` | Certificados do provedor |
| `GOOGLE_SAVE_TOKEN_TO_ENV` | `False` | Se `True`, salva tokens OAuth no `.env` |
| `GOOGLE_OAUTH_TOKEN` | vazio | Access token para uso por ambiente |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | vazio | Refresh token para renovar acesso |
| `GOOGLE_OAUTH_SCOPES` | veja `.env.example` | Escopos OAuth autorizados |
| `GOOGLE_OAUTH_EXPIRY` | vazio | Data de expiracao do access token |
| `GOOGLE_DRIVE_FOLDER_ID` | vazio | ID da pasta do Drive para receber uploads |
| `MAX_FILE_SIZE_MB` | `100` | Tamanho maximo por arquivo |
| `ALLOWED_EXTENSIONS` | `pdf,docx,png,...` | Extensoes aceitas no upload |

Escopos usados pelo projeto:

```text
https://www.googleapis.com/auth/drive.file
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/userinfo.profile
openid
```

## Executando o Projeto

Com o ambiente virtual ativo:

```bash
python run.py
```

Abra:

```text
http://localhost:5000
```

Se `PORT=5001`, abra:

```text
http://localhost:5001
```

## Conectar ao Google Drive

Com o servidor rodando, acesse:

```text
http://localhost:5000/auth/google
```

Use a porta configurada no seu `.env`. Faca login com a conta Google que sera usada pelo servidor para receber os arquivos. Ao concluir, o app salva o token em `config/token.json` no modo local.

Para verificar o status:

```text
http://localhost:5000/auth/status
```

Resposta esperada:

```json
{
  "authenticated": true
}
```

## Testando Upload

1. Acesse a tela principal.
2. Selecione ou arraste um arquivo permitido.
3. Clique para enviar ao Drive.
4. Aguarde o progresso concluir.
5. Copie o link gerado.
6. Teste o link em uma aba anonima para confirmar que a permissao publica foi aplicada.

## Docker

Crie o `.env`:

```bash
cp .env.example .env
```

Edite os valores e suba:

```bash
docker compose up --build -d
```

Ver logs:

```bash
docker compose logs -f
```

Parar:

```bash
docker compose down
```

O `Dockerfile` usa Gunicorn:

```text
gunicorn --bind 0.0.0.0:${PORT:-5000} run:app
```

O `docker-compose.yml` expoe a porta configurada em `PORT`.

## Deploy em Servidor

Para Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker

git clone <url-do-repositorio> cartlink
cd cartlink
cp .env.example .env
nano .env

docker compose up --build -d
docker compose logs -f
```

Em producao, use:

- `FLASK_DEBUG=False`.
- `LOCAL_GOOGLE_TEST_MODE=False`.
- `SECRET_KEY` forte.
- HTTPS no dominio publico.
- `OAUTH_REDIRECT_URI` igual a URL cadastrada no Google Cloud.
- Tokens e secrets somente em variaveis de ambiente ou arquivos protegidos no servidor.

## Seguranca e Arquivos Que Nao Devem Ser Enviados

Nunca envie para repositorio publico ou para terceiros:

- `.env`
- `config/credentials.json`
- `config/token.json`
- `venv/`
- `__pycache__/`
- `temp_uploads/`
- logs locais como `*.log`

O `.gitignore` ja cobre os principais arquivos sensiveis do projeto. Antes de enviar, confira:

```bash
git status --short
```

Se for compactar o projeto manualmente, inclua o codigo fonte, `requirements.txt`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `README.md` e `config/README.txt`, mas nao inclua secrets reais.

## Fluxo de Credenciais

O CartoLink 2.0 aceita duas formas de configurar o OAuth:

- Via `.env`, usando `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`.
- Via arquivo `config/credentials.json`, baixado do Google Cloud.

Em modo local, o token autorizado e salvo em:

```text
config/token.json
```

Em deploy, voce pode optar por armazenar tokens em variaveis de ambiente usando `GOOGLE_SAVE_TOKEN_TO_ENV=True`, mas trate esses valores como segredo.

## Solucao de Problemas

### `redirect_uri_mismatch`

A URI configurada no `.env` nao bate exatamente com a cadastrada no Google Cloud. Confira protocolo, dominio, porta e caminho.

### `invalid_grant`

O token antigo foi revogado, expirou ou nao pode mais ser renovado. Remova `config/token.json` e autentique novamente em `/auth/google`.

### `Scope has changed`

Os escopos retornados pelo Google precisam bater com os escopos configurados no app. Confirme se `userinfo.profile` esta presente junto com `drive.file`, `userinfo.email` e `openid`.

### `Admin access required`

Fora do modo local, informe a chave administrativa:

```text
/auth/google?key=SUA_CHAVE
```

Ou envie o header:

```text
X-Admin-Setup-Key: SUA_CHAVE
```

### `credentials.json not found`

Preencha `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no `.env` ou coloque o arquivo `credentials.json` em `config/`.

### Upload retorna erro 503

O Drive ainda nao esta autenticado. Acesse `/auth/google`, conclua o login e verifique `/auth/status`.

### Porta em uso

Altere `PORT` no `.env` e atualize tambem `OAUTH_REDIRECT_URI` e a URI autorizada no Google Cloud.

### `UnicodeEncodeError` no Windows

Se o terminal Windows nao aceitar caracteres do banner, rode com:

```powershell
$env:PYTHONIOENCODING='utf-8'
python run.py
```

## Manutencao

Para atualizar dependencias:

```bash
pip install --upgrade -r requirements.txt
```

Para limpar arquivos temporarios locais:

```bash
rm -rf temp_uploads/*
```

No PowerShell:

```powershell
Remove-Item temp_uploads\* -Force
```

## Licenca

Defina a licenca conforme a necessidade do projeto antes de publicar. Se nao houver arquivo `LICENSE`, trate o codigo como privado.
