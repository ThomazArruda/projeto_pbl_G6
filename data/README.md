# Pasta de Dados

O banco SQLite `clinic.db`, utilizado pelo painel Streamlit, é gravado neste
diretório. Ele contém:

- A lista de pacientes cadastrados (`patients`).
- O histórico de sessões de cada paciente (`sessions`), com os dados da sessão
  serializados em JSON.

O arquivo `.gitignore` está configurado para ignorar automaticamente o banco de
dados e quaisquer exportações (`.json`, `.csv`) que você venha a gerar aqui, de
modo que informações sensíveis não sejam versionadas.
