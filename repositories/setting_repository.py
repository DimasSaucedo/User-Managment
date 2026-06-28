from database.models import Setting
from repositories.base_repository import BaseRepository


class SettingRepository(BaseRepository):

    def create(self, clave, valor):

        setting = Setting(
            clave=clave,
            valor=valor
        )

        self.db.add(setting)
        self.commit()

        return setting

    def get_all(self):
        return (
            self.db.query(Setting)
            .order_by(Setting.clave)
            .all()
        )

    def get(self, clave):
        return (
            self.db.query(Setting)
            .filter(Setting.clave == clave)
            .first()
        )

    def set(self, clave, valor):

        setting = self.get(clave)

        if setting:
            setting.valor = valor
        else:
            setting = Setting(
                clave=clave,
                valor=valor
            )
            self.db.add(setting)

        self.commit()

        return setting

    def delete(self, clave):

        setting = self.get(clave)

        if not setting:
            return False

        self.db.delete(setting)
        self.commit()

        return True