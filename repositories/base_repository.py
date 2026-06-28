from database.database import SessionLocal


class BaseRepository:

    def __init__(self):
        self.db = SessionLocal()

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()