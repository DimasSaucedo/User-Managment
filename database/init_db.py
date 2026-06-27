from database.database import Base, engine

# Importa todos los modelos para que SQLAlchemy los registre
import database.models


def init_database():
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos creada correctamente.")


if __name__ == "__main__":
    init_database()