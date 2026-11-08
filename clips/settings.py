import json

from PySide6.QtCore import QObject, Signal

from .paths import data_dir

DEFAULTS = {
    "language": "auto",          # auto | en | id
    "run_at_startup": True,
    "accent_follow": True,
    "max_items": 500,
    "save_images": True,
    "clear_on_exit": False,
    "hotkey": "ctrl+shift+v",
    "detect_enabled": False,     # email/password detection, off by default
    "show_button": "always",     # always | passwords | never
    "button_pos": "br",          # br | bl
    "ignored_apps": [],
    "password_ttl_min": 5,
    "paused": False,
    "first_run": True,
}


class Settings(QObject):
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.path = data_dir() / "settings.json"
        self.data = dict(DEFAULTS)
        try:
            self.data.update(json.loads(self.path.read_text("utf-8")))
        except Exception:
            pass

    def get(self, key):
        return self.data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        if self.data.get(key) == value:
            return
        self.data[key] = value
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2), "utf-8")
            tmp.replace(self.path)
        except Exception:
            pass
        self.changed.emit(key)
