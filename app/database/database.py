from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 👇 ESTO ES LO QUE TE FALTA
Base = declarative_base()

def run_migrations():
    """Crea tablas si no existen y agrega columnas nuevas (SQLite no soporta ALTER TABLE automático)."""
    # Primero crear todas las tablas definidas en los modelos
    import app.database.models  # asegura que los modelos estén registrados en Base
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Obtener columnas actuales de servers
        result = conn.execute(
            __import__("sqlalchemy").text("PRAGMA table_info(servers)")
        )
        existing = {row[1] for row in result}

        migrations = [
            ("ssh_username", "VARCHAR(100)"),
            ("ssh_password", "VARCHAR(255)"),
            ("ultima_conexion", "DATETIME"),
        ]
        for col, col_type in migrations:
            if col not in existing:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE servers ADD COLUMN {col} {col_type}"
                    )
                )
        conn.commit()