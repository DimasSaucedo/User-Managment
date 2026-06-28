from app.database.database import engine, Base
from app.database import models  # IMPORTANTE: registra los modelos


def init_db():
    Base.metadata.create_all(bind=engine)