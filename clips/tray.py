from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import winutil
from .i18n import i18n, tr
from .paths import resource
from .theme import icon


class GlassMenu(QMenu):
    def __init__(self):
        super().__init__()
        from PySide6.QtCore import Qt
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def showEvent(self, e):
        super().showEvent(e)
        winutil.apply_acrylic(int(self.winId()), (22, 23, 30, 150))


class Tray(QObject):
    open_requested = Signal()
    settings_requested = Signal()
    about_requested = Signal()
    quit_requested = Signal()
    clear_requested = Signal()
    pause_toggled = Signal(bool)
    startup_toggled = Signal(bool)

    def __init__(self, settings):
        super().__init__()
        self.s = settings
        self.icon = QSystemTrayIcon(QIcon(resource("assets/icon.png")))
        self.menu = GlassMenu()
        self.a_open = self.menu.addAction("")
        self.a_pause = self.menu.addAction("")
        self.a_pause.setCheckable(True)
        self.a_clear = self.menu.addAction("")
        self.menu.addSeparator()
        self.a_startup = self.menu.addAction("")
        self.a_startup.setCheckable(True)
        self.a_settings = self.menu.addAction("")
        self.a_about = self.menu.addAction("")
        self.menu.addSeparator()
        self.a_quit = self.menu.addAction("")
        self.a_open.triggered.connect(self.open_requested)
        self.a_pause.toggled.connect(self.pause_toggled)
        self.a_clear.triggered.connect(self.clear_requested)
        self.a_startup.toggled.connect(self.startup_toggled)
        self.a_settings.triggered.connect(self.settings_requested)
        self.a_about.triggered.connect(self.about_requested)
        self.a_quit.triggered.connect(self.quit_requested)
        self.menu.aboutToShow.connect(self._sync)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(
            lambda r: self.open_requested.emit() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        i18n.changed.connect(self.retranslate)
        self.retranslate()

    def _sync(self):
        for act, key in ((self.a_pause, "paused"), (self.a_startup, "run_at_startup")):
            act.blockSignals(True)
            act.setChecked(bool(self.s.get(key)))
            act.blockSignals(False)

    def retranslate(self):
        from . import hotkey
        keys = "+".join(hotkey.pretty(self.s.get("hotkey")))
        self.a_open.setText(f"{tr('tray_open')}\t{keys}")
        self.a_pause.setText(tr("tray_pause"))
        self.a_clear.setText(tr("tray_clear"))
        self.a_startup.setText(tr("tray_startup"))
        self.a_settings.setText(tr("tray_settings"))
        self.a_about.setText(tr("tray_about"))
        self.a_quit.setText(tr("tray_quit"))

    def show(self):
        self.icon.show()

    def message(self, text):
        self.icon.showMessage("Clips", text, QSystemTrayIcon.MessageIcon.Information, 4000)
