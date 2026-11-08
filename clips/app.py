import sys
import time

from PySide6.QtCore import QBuffer, QByteArray, QCoreApplication, QDir, QIODevice, QLockFile, QMimeData, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import QFont, QGuiApplication, QIcon, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

from . import detect, hotkey, winutil
from .about import AboutWindow
from .db import Database
from .detected import DetectedWindow, Toast
from .i18n import i18n, tr
from .paths import data_dir, resource
from .popup import PopupWindow
from .settings import Settings
from .settings_window import SettingsWindow
from .theme import build_qss, theme
from .tray import Tray

HOTKEY_ID = 0xC11B
EXCLUDE_FMT = "ExcludeClipboardContentFromMonitorProcessing"
IPC_NAME = "clips-app-ipc"


class Controller:
    def __init__(self, app: QApplication):
        self.app = app
        self.s = Settings()
        self.db = Database(data_dir() / "clips.db")
        i18n.set_pref(self.s.get("language"))
        self._refresh_accent()
        app.setStyleSheet(build_qss())
        theme.changed.connect(lambda: app.setStyleSheet(build_qss()))

        self.popup = PopupWindow(self.db, self.s)
        self.settings_win = SettingsWindow(self.s)
        self.about_win = AboutWindow()
        self.detected = DetectedWindow(self.db)
        self.toast = Toast(self.s)
        self.tray = Tray(self.s)
        self.prev_hwnd = 0
        self._ignore_until = 0.0

        # wiring
        self.popup.chosen.connect(self.paste_item)
        self.popup.settings_requested.connect(self.show_settings)
        self.popup.language_chosen.connect(lambda c: self.s.set("language", c))
        self.settings_win.about_requested.connect(self.show_about)
        self.settings_win.quit_requested.connect(app.quit)
        self.detected.copy_requested.connect(self.copy_item)
        self.toast.view_clicked.connect(self.show_detected)
        self.tray.open_requested.connect(self.open_popup)
        self.tray.settings_requested.connect(self.show_settings)
        self.tray.about_requested.connect(self.show_about)
        self.tray.quit_requested.connect(app.quit)
        self.tray.clear_requested.connect(lambda: self.db.clear(keep_pinned=True))
        self.tray.pause_toggled.connect(lambda v: self.s.set("paused", v))
        self.tray.startup_toggled.connect(lambda v: self.s.set("run_at_startup", v))
        self.s.changed.connect(self.on_setting)
        app.aboutToQuit.connect(self.cleanup)

        # clipboard (debounced: Windows often fires several change events per copy)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(80)
        self._debounce.timeout.connect(self.on_clipboard)
        QGuiApplication.clipboard().dataChanged.connect(self._debounce.start)

        # global hotkey
        self._filter = hotkey.HotkeyFilter(lambda _id: self.toggle_popup() if _id == HOTKEY_ID else None)
        app.installNativeEventFilter(self._filter)
        self.bind_hotkey()

        # housekeeping: expire passwords
        self._purge = QTimer()
        self._purge.timeout.connect(self.db.purge_expired)
        self._purge.start(15000)

        # a second launch (Start menu / shortcut) pings us to open the history popup
        QLocalServer.removeServer(IPC_NAME)
        self.server = QLocalServer()
        self.server.listen(IPC_NAME)
        self.server.newConnection.connect(self._on_ipc)

        self.tray.show()
        self.first_run()

    def _on_ipc(self):
        conn = self.server.nextPendingConnection()
        if conn is not None:
            conn.readyRead.connect(lambda c=conn: (c.readAll(), QTimer.singleShot(0, self.open_popup), c.disconnectFromServer()))

    # ------------------------------------------------------------ setup
    def first_run(self):
        if not self.s.get("first_run"):
            return
        box = QMessageBox(QMessageBox.Icon.Question, tr("first_title"), tr("first_body"),
                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText(tr("yes"))
        box.button(QMessageBox.StandardButton.No).setText(tr("no"))
        box.setDefaultButton(QMessageBox.StandardButton.Yes)
        box.setWindowIcon(QIcon(resource("assets/icon.png")))
        self.s.set("run_at_startup", box.exec() == QMessageBox.StandardButton.Yes)
        self.s.set("first_run", False)
        self.tray.message(tr("running_msg", k="+".join(hotkey.pretty(self.s.get("hotkey")))))

    def _refresh_accent(self):
        theme.set_accent(winutil.accent_color() if self.s.get("accent_follow") else "#3EC9A7")

    def bind_hotkey(self):
        hotkey.unregister(HOTKEY_ID)
        if not hotkey.register(HOTKEY_ID, self.s.get("hotkey")) and winutil.IS_WIN:
            self.tray.message(tr("hk_taken", k="+".join(hotkey.pretty(self.s.get("hotkey")))))

    def on_setting(self, key):
        if key == "language":
            i18n.set_pref(self.s.get("language"))
            self.tray.retranslate()
        elif key == "hotkey":
            self.bind_hotkey()
            self.tray.retranslate()
        elif key == "run_at_startup":
            winutil.set_run_at_startup(bool(self.s.get(key)))
        elif key == "accent_follow":
            self._refresh_accent()
        elif key == "max_items":
            self.db.trim(self.s.get(key))

    def cleanup(self):
        hotkey.unregister(HOTKEY_ID)
        if self.s.get("clear_on_exit"):
            self.db.clear(keep_pinned=True)
        else:
            self.db.purge_expired()

    # ---------------------------------------------------------- windows
    def _remember_foreground(self):
        hwnd = winutil.foreground_window()
        ours = {int(w.winId()) for w in (self.popup, self.settings_win, self.about_win, self.detected)
                if w.isVisible()}
        if hwnd and hwnd not in ours:
            self.prev_hwnd = hwnd

    def open_popup(self):
        self._remember_foreground()
        self._refresh_accent()
        self.popup.open_at_cursor()

    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide_animated()
        else:
            self.open_popup()

    def _center(self, win):
        g = QGuiApplication.primaryScreen().availableGeometry()
        from PySide6.QtCore import QPoint
        return QPoint(g.center().x() - win.width() // 2, g.center().y() - win.height() // 2)

    def show_settings(self):
        self.popup.hide_animated()
        self.settings_win.show_animated(None if self.settings_win.isVisible() else self._center(self.settings_win))

    def show_about(self):
        self.about_win.show_animated(None if self.about_win.isVisible() else self._center(self.about_win))

    def show_detected(self):
        self.detected.show_animated(None if self.detected.isVisible() else self._center(self.detected))

    # -------------------------------------------------------- clipboard
    def _set_clipboard(self, row, sensitive=False):
        md = QMimeData()
        if row["kind"] == "image":
            md.setImageData(QImage.fromData(row["image"]))
        elif row["kind"] == "password":
            md.setText(winutil.decrypt_text(row["content"]))
        else:
            md.setText(row["content"])
        if sensitive:  # ask other clipboard managers/history not to keep it
            md.setData(EXCLUDE_FMT, QByteArray(b"1"))
        self._ignore_until = time.monotonic() + 0.8
        QGuiApplication.clipboard().setMimeData(md)

    def paste_item(self, item_id):
        row = self.db.get(item_id)
        if not row:
            return
        self._set_clipboard(row)
        self.db.touch(item_id)
        self.popup.hide_animated()
        QTimer.singleShot(160, lambda h=self.prev_hwnd: winutil.paste_into(h))

    def copy_item(self, item_id):
        row = self.db.get(item_id)
        if row:
            self._set_clipboard(row, sensitive=row["kind"] == "password")

    def on_clipboard(self):
        if time.monotonic() < self._ignore_until or self.s.get("paused"):
            return
        exe = winutil.process_name_of(winutil.foreground_window())
        if exe and exe in [a.lower() for a in self.s.get("ignored_apps")]:
            return
        sensitive = winutil.clipboard_is_sensitive()
        md = QGuiApplication.clipboard().mimeData()
        if md is None:
            return
        detect_on = bool(self.s.get("detect_enabled"))
        if md.hasText() and md.text().strip():
            text = md.text()
            kind = detect.classify(text, sensitive) if detect_on else "text"
            if sensitive and not detect_on:
                return  # never keep what a password manager marked as private
            if kind == "password":
                ttl = max(1, int(self.s.get("password_ttl_min")))
                self.db.add("password", content=winutil.encrypt_text(text), expires=time.time() + ttl * 60)
            else:
                self.db.add(kind, content=text)
            self.db.trim(self.s.get("max_items"))
            self._maybe_toast(kind)
        elif md.hasImage() and self.s.get("save_images") and not sensitive:
            img = QGuiApplication.clipboard().image()
            if img.isNull():
                return
            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buf, "PNG")
            self.db.add("image", image=bytes(buf.data()))
            self.db.trim(self.s.get("max_items"))
        if self.detected.isVisible():
            self.detected.refresh()

    def _maybe_toast(self, kind):
        mode = self.s.get("show_button")
        if not self.s.get("detect_enabled") or mode == "never" or kind == "text":
            return
        if mode == "passwords" and kind != "password":
            return
        self.toast.present(kind)


def main():
    QCoreApplication.setApplicationName("Clips")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(resource("assets/icon.png")))
    app.setFont(QFont("Segoe UI", 10))
    # already running? ask that instance to show its popup, then leave
    probe = QLocalSocket()
    probe.connectToServer(IPC_NAME)
    if probe.waitForConnected(200):
        probe.write(b"show")
        probe.flush()
        probe.waitForBytesWritten(500)
        sys.exit(0)
    lock = QLockFile(QDir.temp().filePath("clips-app.lock"))
    if not lock.tryLock(100):
        sys.exit(0)
    ctl = Controller(app)
    if "--background" not in sys.argv:  # launched by hand: show the history right away
        QTimer.singleShot(500, ctl.open_popup)
    sys.exit(app.exec())
