from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QKeySequenceEdit, QLabel,
                               QLineEdit, QListWidget, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from . import __version__, hotkey
from .i18n import i18n, tr
from .theme import GlassWindow, HLine, TitleBar, ToggleSwitch, clear_layout, icon


class HotkeyDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.value = None
        self.setWindowTitle(tr("hk_title"))
        self.setMinimumWidth(380)
        v = QVBoxLayout(self)
        v.setSpacing(12)
        hint = QLabel(tr("hk_hint"))
        hint.setWordWrap(True)
        self.edit = QKeySequenceEdit()
        self.msg = QLabel("")
        self.msg.setObjectName("muted")
        self.msg.setWordWrap(True)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        box.button(QDialogButtonBox.StandardButton.Save).setText(tr("save"))
        box.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        box.accepted.connect(self._ok)
        box.rejected.connect(self.reject)
        for w in (hint, self.edit, self.msg, box):
            v.addWidget(w)

    def _ok(self):
        s = hotkey.sequence_to_string(self.edit.keySequence())
        if not s:
            self.msg.setText(tr("hk_invalid"))
            return
        self.value = s
        self.accept()


class IgnoredDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.s = settings
        self.setWindowTitle(tr("ign_title"))
        self.setMinimumSize(380, 340)
        v = QVBoxLayout(self)
        v.setSpacing(10)
        hint = QLabel(tr("ign_hint"))
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        self.list = QListWidget()
        self.list.addItems(settings.get("ignored_apps"))
        row = QHBoxLayout()
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(tr("ign_ph"))
        self.edit.returnPressed.connect(self._add)
        add = QPushButton(tr("ign_add"))
        add.setObjectName("ghost")
        add.clicked.connect(self._add)
        row.addWidget(self.edit, 1)
        row.addWidget(add)
        rem = QPushButton(tr("ign_remove"))
        rem.setObjectName("ghost")
        rem.clicked.connect(self._remove)
        done = QPushButton(tr("close"))
        done.setObjectName("primary")
        done.clicked.connect(self.accept)
        for w in (hint, self.list):
            v.addWidget(w)
        v.addLayout(row)
        v.addWidget(rem)
        v.addWidget(done)

    def _save(self):
        self.s.set("ignored_apps", [self.list.item(i).text() for i in range(self.list.count())])

    def _add(self):
        name = self.edit.text().strip().lower()
        if name and name not in [self.list.item(i).text() for i in range(self.list.count())]:
            self.list.addItem(name)
            self._save()
        self.edit.clear()

    def _remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self._save()


class SettingsWindow(GlassWindow):
    about_requested = Signal()
    quit_requested = Signal()

    def __init__(self, settings):
        super().__init__()
        self.s = settings
        self.setFixedSize(480, 660)
        self._texts, self._combos = [], []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.title = TitleBar("settings", self)
        root.addWidget(self.title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        self.form = QVBoxLayout(body)
        self.form.setContentsMargins(20, 0, 20, 8)
        self.form.setSpacing(0)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        # ---- General
        self._section("sec_general")
        self.cmb_lang = self._combo("language", [("auto", "lang_auto", {}), ("en", "lang_en", {}), ("id", "lang_id", {})])
        self._row("set_language", self.cmb_lang)
        self.t_startup = self._toggle("run_at_startup")
        self._row("set_startup", self.t_startup)
        self.t_accent = self._toggle("accent_follow")
        self._row("set_accent", self.t_accent)
        # ---- History
        self._section("sec_history")
        self.cmb_keep = self._combo("max_items", [(n, "items_n", {"n": n}) for n in (100, 250, 500, 1000, 2000)])
        self._row("set_keep", self.cmb_keep)
        self.t_images = self._toggle("save_images")
        self._row("set_images", self.t_images)
        self.t_clear = self._toggle("clear_on_exit")
        self._row("set_clear_exit", self.t_clear)
        # ---- Shortcut & privacy
        self._section("sec_shortcut")
        self.hk_box = QHBoxLayout()
        self.hk_box.setSpacing(6)
        self.btn_change = QPushButton()
        self.btn_change.setObjectName("ghost")
        self.btn_change.clicked.connect(self._change_hotkey)
        self._row("set_hotkey", self.hk_box, self.btn_change, change_btn=True)
        self.t_detect = self._toggle("detect_enabled")
        self._row("set_detect", self.t_detect)
        self.cmb_btn = self._combo("show_button", [("always", "btn_always", {}), ("passwords", "btn_pw", {}), ("never", "btn_never", {})])
        self._row("set_show_btn", self.cmb_btn)
        self.cmb_pos = self._combo("button_pos", [("br", "pos_br", {}), ("bl", "pos_bl", {})])
        self._row("set_btn_pos", self.cmb_pos)
        self.btn_ign = QPushButton()
        self.btn_ign.setObjectName("ghost")
        self.btn_ign.clicked.connect(lambda: IgnoredDialog(self, self.s).exec())
        self._row("set_ignored", self.btn_ign)
        self.form.addStretch(1)

        # ---- footer: About + version
        root.addWidget(HLine())
        foot = QHBoxLayout()
        foot.setContentsMargins(20, 12, 20, 12)
        foot.setSpacing(14)
        self.btn_about = QPushButton()
        self.btn_about.setObjectName("ghost")
        self.btn_about.setIcon(icon("info", "#e8e9ee", 18))
        self.btn_about.setMinimumHeight(40)
        self.btn_about.clicked.connect(self.about_requested)
        self.lbl_ver = QLabel()
        self.lbl_ver.setObjectName("muted")
        foot.addWidget(self.btn_about)
        foot.addWidget(self.lbl_ver)
        foot.addStretch()
        self.btn_quit = QPushButton()
        self.btn_quit.setObjectName("ghost")
        self.btn_quit.setIcon(icon("power", "#e8e9ee", 16))
        self.btn_quit.setMinimumHeight(40)
        self.btn_quit.clicked.connect(self.quit_requested)
        foot.addWidget(self.btn_quit)
        root.addLayout(foot)

        i18n.changed.connect(self.retranslate)
        self.retranslate()

    # --------------------------------------------------------- builders
    def _section(self, key):
        lb = QLabel()
        lb.setObjectName("section")
        lb.setStyleSheet("padding:14px 0 4px 4px")
        self._texts.append((lb, key))
        self.form.addWidget(lb)

    def _row(self, key, *controls, change_btn=False):
        w = QWidget()
        w.setMinimumHeight(40)
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 0, 4, 0)
        h.setSpacing(6)
        lb = QLabel()
        self._texts.append((lb, key))
        h.addWidget(lb, 1)
        for c in controls:
            h.addLayout(c) if hasattr(c, "addWidget") and not isinstance(c, QWidget) else h.addWidget(c)
        self.form.addWidget(w)

    def _toggle(self, key):
        t = ToggleSwitch(bool(self.s.get(key)))
        t.toggled.connect(lambda on, k=key: self.s.set(k, on))
        return t

    def _combo(self, key, spec):
        c = QComboBox()
        c.setCursor(Qt.CursorShape.PointingHandCursor)
        c.currentIndexChanged.connect(lambda _i, k=key, cb=c: self.s.set(k, cb.currentData()))
        self._combos.append((c, key, spec))
        return c

    # ------------------------------------------------------------ state
    def _fill_combos(self):
        for c, key, spec in self._combos:
            c.blockSignals(True)
            c.clear()
            for value, tkey, kw in spec:
                c.addItem(tr(tkey, **kw), value)
            idx = c.findData(self.s.get(key))
            c.setCurrentIndex(max(0, idx))
            c.blockSignals(False)

    def _show_hotkey(self):
        clear_layout(self.hk_box)
        for part in hotkey.pretty(self.s.get("hotkey")):
            k = QLabel(part)
            k.setObjectName("kbd")
            k.setFixedHeight(24)
            self.hk_box.addWidget(k, 0, Qt.AlignmentFlag.AlignVCenter)

    def sync(self):
        for t, key in ((self.t_startup, "run_at_startup"), (self.t_accent, "accent_follow"),
                       (self.t_images, "save_images"), (self.t_clear, "clear_on_exit"),
                       (self.t_detect, "detect_enabled")):
            t.set_silently(bool(self.s.get(key)))
        self._fill_combos()
        self._show_hotkey()

    def retranslate(self):
        for lb, key in self._texts:
            lb.setText(tr(key))
        self.btn_change.setText(tr("change"))
        self.btn_ign.setText(tr("manage"))
        self.btn_about.setText(tr("about"))
        self.btn_quit.setText(tr("quit_app"))
        self.lbl_ver.setText(tr("version", v=__version__))
        self.title.retranslate()
        self.sync()

    def showEvent(self, e):
        self.sync()
        super().showEvent(e)

    def _change_hotkey(self):
        dlg = HotkeyDialog(self)
        if dlg.exec() and dlg.value:
            self.s.set("hotkey", dlg.value)
            self._show_hotkey()
