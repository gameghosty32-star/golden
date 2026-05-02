from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


def ensure_database_schema():
    """Adiciona colunas de população ausentes em tabelas SQLite existentes."""
    def ensure_column(table_name, column_name):
        existing_columns = [row[1] for row in db.session.execute(text(f"PRAGMA table_info({table_name})"))]
        if column_name not in existing_columns:
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER"))
            db.session.commit()

    ensure_column('provincia', 'population')
    ensure_column('municipio', 'population')
    ensure_column('bairro', 'population')
    ensure_column('rua', 'population')
