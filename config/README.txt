# Este arquivo existe para garantir que a pasta config/ seja criada no repositorio.
#
# Coloque aqui o arquivo credentials.json baixado do Google Cloud Console.
# O arquivo token.json sera criado apos a autorizacao da conta principal usada pelo servidor.
#
# Usuarios finais nao precisam fazer login no site. O backend reutiliza token.json
# para enviar os arquivos com a conta principal do Google Drive.
# Para a autorizacao inicial, use a rota /auth/google com o valor atual de ADMIN_SETUP_KEY definido no arquivo .env.
#
# NUNCA faca commit de credentials.json ou token.json!
