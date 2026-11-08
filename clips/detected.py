import time

from PySide6.QtCore import QPoint, QTimer, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from . import winutil
from .db import Database
from .i18n import i18n, tr
from .popup import ago
from .theme import ElidedLabel, GlassWindow, HLine, IconButton, TitleBar, clear_layout, icon, pixmap, theme


class DetectedRow(QWidget):
    copy_requested = Signal(int)

    def __init__(self, row, secret: bool):
        super().__init__()
        self.item_id, self.secret, self.plain, self.shown = row["id"], secret, "", False
        self.setFixedHeight(56)
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 0, 4, 0)
        h.setSpacing(4)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 8, 0, 8)
        if secret:
            self.plain = winutil.decrypt_text(row["content"])
            self.title = ElidedLabel("•" * 12, "#e8e9ee", 16, spacing=3.0)
        else:
            self.title = ElidedLabel(row["content"] or "", "#e8e9ee", 14)
        meta = QLabel(tr("det_copied", t=ago(row["created"])))
        meta.setObjectName("muted")
        col.addWidget(self.title)
        col.addWidget(meta)
        h.addLayout(col, 1)
        if secret:
            self.eye = IconButton("eye", 40, 18)
            self.eye.clicked.connect(self._toggle)
            self.eye.setToolTip(tr("det_show"))
            h.addWidget(self.eye)
        cp = IconButton("copy", 40, 18)
        cp.setToolTip(tr("det_copy"))
        cp.clicked.connect(lambda: self.copy_requested.emit(self.item_id))
        h.addWidget(cp)

    def _toggle(self):
        self.shown = not self.shown
        self.title.setText(self.plain if self.shown else "•" * 12)
        self.eye.set_icon("eyeoff" if self.shown else "eye")
        if self.shown:
            QTimer.singleShot(6000, self._hide_again)

    def _hide_again(self):
        if self.shown:
            self._toggle()


class DetectedWindow(GlassWindow):
    copy_requested = Signal(int)

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setFixedSize(440, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.title = TitleBar("det_title", self)
        root.addWidget(self.title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.lay = QVBoxLayout(self.body)
        self.lay.setContentsMargins(12, 0, 12, 8)
        self.lay.setSpacing(0)
        scroll.setWidget(self.body)
        root.addWidget(scroll, 1)
        root.addWidget(HLine())
        foot = QHBoxLayout()
        foot.setContentsMargins(16, 12, 16, 12)
        foot.setSpacing(8)
        lock = QLabel()
        lock.setPixmap(pixmap("lock", "#b4b6c2", 14))
        self.note = QLabel()
        self.note.setObjectName("muted")
        foot.addWidget(lock)
        foot.addWidget(self.note, 1)
        root.addLayout(foot)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.clears = None
        i18n.changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self):
        self.note.setText(tr("det_note"))
        self.title.retranslate()
        if self.isVisible():
            self.refresh()

    def _header(self, key, right=None):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 12, 0)
        lb = QLabel(tr(key))
        lb.setObjectName("section")
        h.addWidget(lb)
        h.addStretch()
        if right is not None:
            h.addWidget(right)
        return w

    def refresh(self):
        self.db.purge_expired()
        clear_layout(self.lay)
        emails, pws = self.db.by_kind("email"), self.db.passwords_rows() if hasattr(self.db, "passwords_rows") else self.db.by_kind("password")
        self.lay.addWidget(self._header("det_emails"))
        self._rows(emails, False)
        sp = QWidget()
        sp.setFixedHeight(12)
        self.lay.addWidget(sp)
        self.lay.addWidget(HLine())
        self.clears = QLabel()
        self.clears.setObjectName("muted")
        self.lay.addWidget(self._header("det_passwords", self.clears))
        self._expiries = [r["expires"] for r in pws if r["expires"]]
        self._rows(pws, True)
        self.lay.addStretch(1)
        self._tick()

    def _rows(self, rows, secret):
        if not rows:
            lb = QLabel(tr("det_none"))
            lb.setObjectName("muted")
            lb.setContentsMargins(12, 10, 0, 10)
            self.lay.addWidget(lb)
            return
        for r in rows:
            w = DetectedRow(r, secret)
            w.copy_requested.connect(self.copy_requested)
            self.lay.addWidget(w)

    def _tick(self):
        if self.clears is None:
            return
        if getattr(self, "_expiries", None):
            left = max(0, int(min(self._expiries) - time.time()))
            self.clears.setText(tr("det_clears", t=f"{left // 60}:{left % 60:02d}"))
            if left == 0:
                QTimer.singleShot(200, self.refresh)
        else:
            self.clears.setText("")

    def showEvent(self, e):
        self.refresh()
        self.timer.start(1000)
        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)


class Toast(GlassWindow):
    """Small floating button that appears near the taskbar when something is detected."""
    view_clicked = Signal()
    SHOW_MS = 6000

    def __init__(self, settings):
        super().__init__(popup=True, no_focus=True)
        self.s = settings
        self.setFixedSize(300, 66)
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 0, 12, 4)
        h.setSpacing(12)
        self.icon = QLabel()
        col = QVBoxLayout()
        col.setSpacing(1)
        self.title = QLabel()
        self.title.setStyleSheet("font-weight:600;font-size:14px")
        self.sub = QLabel()
        self.sub.setObjectName("muted")
        col.addStretch()
        col.addWidget(self.title)
        col.addWidget(self.sub)
        col.addStretch()
        self.btn = QPushButton()
        self.btn.setObjectName("primary")
        self.btn.setMinimumHeight(36)
        self.btn.setStyleSheet("padding:0 16px;min-height:36px;font-size:13px;border-radius:8px")
        self.btn.clicked.connect(self._clicked)
        h.addWidget(self.icon)
        h.addLayout(col, 1)
        h.addWidget(self.btn)
        self.progress = 1.0
        self.bar = QVariantAnimation(self)
        self.bar.setStartValue(1.0)
        self.bar.setEndValue(0.0)
        self.bar.setDuration(self.SHOW_MS)
        self.bar.valueChanged.connect(self._bar)
        self.bar.finished.connect(self.hide_animated)

    def _bar(self, v):
        self.progress = float(v)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRect(1, self.height() - 4, self.width() - 2, 3)
        p.setBrush(theme.accent)
        p.drawRect(1, self.height() - 4, int((self.width() - 2) * self.progress), 3)

    def _clicked(self):
        self.bar.stop()
        self.hide_animated()
        self.view_clicked.emit()

    def present(self, kind: str):
        self.icon.setPixmap(pixmap("lock" if kind == "password" else "mail", theme.accent.name(), 20))
        self.title.setText(tr("toast_pw" if kind == "password" else "toast_email"))
        self.sub.setText(tr("toast_sub"))
        self.btn.setText(tr("toast_view"))
        g = (QGuiApplication.primaryScreen()).availableGeometry()
        left = self.s.get("button_pos") == "bl"
        x = g.left() + 16 if left else g.right() - self.width() - 16
        y = g.bottom() - self.height() - 16
        self.bar.stop()
        self.progress = 1.0
        self.show_animated(QPoint(x, y), offset=QPoint(-28 if left else 28, 0), activate=False)
        self.bar.start()
