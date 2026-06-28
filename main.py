from repositories.setting_repository import SettingRepository

repo = SettingRepository()

repo.set("theme", "dark")
repo.set("window_width", "1400")

for setting in repo.get_all():
    print(setting.clave, setting.valor)