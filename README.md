# Golden Project

## Descrição

O Golden Project é uma aplicação web desenvolvida em Flask para gerenciamento de localizações geográficas. Permite o cadastro e administração de províncias, municípios, bairros e ruas, além de funcionalidades de autenticação de usuários (login e cadastro). É ideal para sistemas de mapeamento ou diretórios locais.

### Funcionalidades Principais
- **Autenticação de Usuários**: Cadastro, login e logout.
- **Gerenciamento de Localizações**:
  - Províncias
  - Municípios (vinculados a províncias)
  - Bairros (vinculados a municípios)
  - Ruas (vinculadas a bairros)
- **Dashboard**: Visualização de feeds e contadores de registros.
- **Busca**: Pesquisa por localidades.
- **Interface Responsiva**: Templates HTML com Bootstrap.

### Tecnologias Utilizadas
- **Backend**: Flask (Python)
- **Banco de Dados**: SQLAlchemy com SQLite (desenvolvimento) ou PostgreSQL (produção)
- **Frontend**: HTML, CSS, JavaScript com Bootstrap
- **Autenticação**: Werkzeug para hashing de senhas
- **Deploy**: Suporte a Docker, Heroku, Railway, Render

## Instalação e Desenvolvimento Local

### Pré-requisitos
- Python 3.9+
- Git

### Passos
1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd golden
   ```

2. **Crie um ambiente virtual**:
   ```bash
   python -m venv .venv
   ```

3. **Ative o ambiente virtual**:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Execute a aplicação**:
   ```bash
   python main.py
   ```
   Acesse em `http://localhost:5000`.

6. **Configuração do Banco de Dados**:
   - O banco SQLite é criado automaticamente em `instance/db.db`.
   - Para desenvolvimento, edite `app/__init__.py` ou use variáveis de ambiente.

## Deploy

### Variáveis de Ambiente Necessárias
Configure as seguintes variáveis em sua plataforma de deploy:
- `SECRET_KEY`: Chave secreta para sessões Flask (gere uma aleatória).
- `SQLALCHEMY_DATABASE_URI`: URI do banco de dados (ex: `postgresql://user:pass@host/db` para produção).
- `FLASK_ENV`: Defina como `production`.

### 1. Deploy no Heroku

1. **Instale o Heroku CLI** e faça login:
   ```bash
   heroku login
   ```

2. **Crie uma aplicação Heroku**:
   ```bash
   heroku create nome-da-sua-app
   ```

3. **Configure variáveis de ambiente**:
   ```bash
   heroku config:set SECRET_KEY=your_secret_key_here
   heroku config:set SQLALCHEMY_DATABASE_URI=postgresql://...
   heroku config:set FLASK_ENV=production
   ```

4. **Adicione um add-on de banco PostgreSQL** (opcional, mas recomendado):
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
   Copie a DATABASE_URL fornecida e configure como `SQLALCHEMY_DATABASE_URI`.

5. **Faça deploy**:
   ```bash
   git push heroku main
   ```

6. **Acesse a aplicação**:
   ```bash
   heroku open
   ```

### 2. Deploy no Railway

1. **Acesse o Railway** e conecte seu repositório GitHub.

2. **Configure variáveis de ambiente** na aba "Variables":
   - `SECRET_KEY`
   - `SQLALCHEMY_DATABASE_URI` (use o banco PostgreSQL integrado do Railway)

3. **Deploy automático**: Railway detectará o `Procfile` e fará o deploy.

4. **Acesse a URL fornecida**.

### 3. Deploy no Render

1. **Acesse o Render** e conecte seu repositório GitHub.

2. **Crie um novo Web Service** e selecione Python.

3. **Configure**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Environment**: Python 3

4. **Adicione variáveis de ambiente**:
   - `SECRET_KEY`
   - `SQLALCHEMY_DATABASE_URI` (use o banco PostgreSQL do Render)

5. **Deploy**: Render fará automaticamente.

6. **Acesse a URL**.

### 4. Deploy com Docker

1. **Construa a imagem**:
   ```bash
   docker build -t golden-app .
   ```

2. **Execute o container**:
   ```bash
   docker run -p 8000:8000 golden-app
   ```

3. **Para produção**, use Docker Compose:
   ```bash
   docker-compose up
   ```

## Tutorial: Mudando o Banco de Dados de SQLite para PostgreSQL

Por padrão, a aplicação usa SQLite para desenvolvimento. Para produção, recomendamos PostgreSQL por ser mais robusto e escalável.

### Passos

1. **Instale o driver PostgreSQL**:
   Adicione ao `requirements.txt`:
   ```
   psycopg2-binary>=2.9
   ```
   Instale: `pip install psycopg2-binary`

2. **Configure a URI do Banco**:
   - Em produção, defina `SQLALCHEMY_DATABASE_URI` como:
     ```
     postgresql://usuario:senha@host:porta/banco
     ```
     Exemplo: `postgresql://user:pass@localhost:5432/golden_db`

3. **Migre os Dados (Opcional)**:
   - Instale `flask-migrate` para migrações:
     ```
     pip install flask-migrate
     ```
   - Inicialize migrações:
     ```bash
     flask db init
     flask db migrate -m "Initial migration"
     flask db upgrade
     ```
   - Para migrar de SQLite para PostgreSQL, exporte dados do SQLite e importe no PostgreSQL usando ferramentas como `pgloader` ou scripts Python.

4. **Teste Localmente**:
   - Configure uma instância local de PostgreSQL (ex: via Docker).
   - Atualize `app/__init__.py` ou use `.env` para testar.

5. **Em Produção**:
   - Use os bancos integrados das plataformas (Heroku Postgres, Railway Postgres, etc.).
   - Certifique-se de que as tabelas sejam criadas automaticamente via `db.create_all()`.

### Notas
- SQLite é adequado apenas para desenvolvimento/teste devido a limitações de concorrência.
- Para migração completa, considere usar Alembic para migrações de schema.

## Contribuição

1. Fork o projeto.
2. Crie uma branch para sua feature: `git checkout -b feature/nova-feature`.
3. Commit suas mudanças: `git commit -m 'Adiciona nova feature'`.
4. Push para a branch: `git push origin feature/nova-feature`.
5. Abra um Pull Request.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.