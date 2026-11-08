import time

from PySide6.QtCore import QEvent, QPoint, QPropertyAnimation, QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QFontMetrics, QGuiApplication, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QGraphicsOpacityEffect, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QPushButton, QScrollArea, QToolButton,
                               QVBoxLayout, QWidget)

from . import winutil
from .i18n import i18n, tr
from .theme import EASE_IN_OUT, EASE_OUT, GlassWindow, IconButton, clear_layout, icon, pixmap, theme

TAB_KEYS = {"all": "tab_all", "text": "tab_text", "image": "tab_images", "pinned": "tab_pinned"}


def ago(ts: float) -> str:
    d = max(0, time.time() - ts)
    if d < 60:
        return tr("now")
    if d < 3600:
        return tr("min_ago", n=int(d // 60))
    if d < 86400:
        return tr("hr_ago", n=int(d // 3600))
    return tr("day_ago", n=int(d // 86400))


class ItemRow(QWidget):
    activated = Signal(int)
    pin_toggled = Signal(int)
    hovered = Signal(object)

    def __init__(self, row):
        super().__init__()
        self.setFixedHeight(56)
        self.setMouseTracking(True)
        self.item_id, self.kind, self.pinned = row["id"], row["kind"], bool(row["pinned"])
        self.thumb = None
        if self.kind == "image":
            img = QImage.fromData(row["image"])
            self.title = tr("image_dim", w=img.width(), h=img.height())
            self.thumb = QPixmap.fromImage(img.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                      Qt.TransformationMode.SmoothTransformation))
        else:
            text = row["content"] or ""
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            self.title = (lines[0] if lines else text.strip() or "…")[:200] + (" ↵" if len(lines) > 1 else "")
        self.meta = f"{tr('kind_' + self.kind)} · {tr('pinned_word') if self.pinned else ago(row['created'])}"
        self.pin = IconButton("pin", 40, 16, self)
        self.pin.clicked.connect(lambda: self.pin_toggled.emit(self.item_id))
        if self.pinned:
            c = theme.accent.name()
            self.pin.set_icon("pin", c, c)
        self.setMouseTracking(True)

    def resizeEvent(self, e):
        self.pin.move(self.width() - 44, 8)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.thumb:
            path = QPainterPath()
            path.addRoundedRect(12, 10, 36, 36, 6, 6)
            p.save()
            p.setClipPath(path)
            p.drawPixmap(QRect(12, 10, 36, 36), self.thumb, self.thumb.rect().adjusted(
                (self.thumb.width() - 72) // 2 if self.thumb.width() > 72 else 0,
                (self.thumb.height() - 72) // 2 if self.thumb.height() > 72 else 0, 0, 0))
            p.restore()
            x = 60
        else:
            p.drawPixmap(14, 20, pixmap("mail" if self.kind == "email" else "text", "#9a9ca8", 16))
            x = 44
        w = max(10, self.width() - x - 52)
        f = self.font()
        f.setPixelSize(14)
        p.setFont(f)
        p.setPen(QColor("#e8e9ee"))
        p.drawText(QRect(x, 9, w, 22), Qt.AlignmentFlag.AlignVCenter,
                   QFontMetrics(f).elidedText(self.title, Qt.TextElideMode.ElideRight, w))
        f.setPixelSize(11)
        p.setFont(f)
        p.setPen(QColor("#b4b6c2"))
        p.drawText(QRect(x, 31, w, 16), Qt.AlignmentFlag.AlignVCenter, self.meta)

    def mouseMoveEvent(self, e):
        self.hovered.emit(self)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.activated.emit(self.item_id)


class KeyHint(QWidget):
    def __init__(self, key, label_key):
        super().__init__()
        self.label_key = label_key
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        k = QLabel(key)
        k.setObjectName("kbd")
        self.label = QLabel()
        self.label.setObjectName("muted")
        lay.addWidget(k)
        lay.addWidget(self.label)
        self.retranslate()

    def retranslate(self):
        self.label.setText(tr(self.label_key))


class PopupWindow(GlassWindow):
    chosen = Signal(int)
    settings_requested = Signal()
    language_chosen = Signal(str)

    def __init__(self, db, settings):
        super().__init__(popup=True)
        self.db, self.s = db, settings
        self.setFixedSize(460, 600)
        self.filter, self.rows, self.sel = "all", [], 0
        self._menu_open, self._opened_at = False, 0.0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        head = QWidget()
        hl = QVBoxLayout(head)
        hl.setContentsMargins(16, 16, 16, 12)
        hl.setSpacing(12)
        r1 = QHBoxLayout()
        r1.setSpacing(8)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.addAction(icon("search", "#9a9ca8", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(lambda _: self.reload())
        self.search.installEventFilter(self)
        self.lang_btn = QToolButton()
        self.lang_btn.setObjectName("lang")
        self.lang_btn.setIcon(icon("globe", "#c9cad3", 16))
        self.lang_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setFixedHeight(44)
        self.lang_btn.clicked.connect(self._lang_menu)
        r1.addWidget(self.search, 1)
        r1.addWidget(self.lang_btn)
        r2 = QHBoxLayout()
        r2.setSpacing(8)
        self.group, self.tabs = QButtonGroup(self), {}
        for key in TAB_KEYS:
            b = QPushButton()
            b.setProperty("chip", True)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, k=key: self._set_filter(k))
            self.group.addButton(b)
            self.tabs[key] = b
            r2.addWidget(b)
        self.tabs["all"].setChecked(True)
        r2.addStretch()
        self.gear = IconButton("gear", 36, 18)
        self.gear.clicked.connect(self.settings_requested)
        r2.addWidget(self.gear)
        hl.addLayout(r1)
        hl.addLayout(r2)
        root.addWidget(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.lay = QVBoxLayout(self.content)
        self.lay.setContentsMargins(8, 0, 8, 8)
        self.lay.setSpacing(0)
        self.hl = QFrame(self.content)
        self.hl.setObjectName("hl")
        self.hl.hide()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        div = QFrame()
        div.setObjectName("divider")
        root.addWidget(div)
        foot = QWidget()
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(16, 12, 16, 12)
        self.hints = [KeyHint("↑↓", "hint_select"), KeyHint("Enter", "hint_paste"),
                      KeyHint("Del", "hint_delete"), KeyHint("Esc", "hint_close")]
        for i, h in enumerate(self.hints):
            fl.addWidget(h)
            if i < len(self.hints) - 1:
                fl.addStretch()
        root.addWidget(foot)

        i18n.changed.connect(self.retranslate)
        theme.changed.connect(lambda: self.reload())
        self.retranslate()

    # -------------------------------------------------------------- text
    def retranslate(self):
        self.search.setPlaceholderText(tr("search_ph"))
        for k, b in self.tabs.items():
            b.setText(tr(TAB_KEYS[k]))
        for h in self.hints:
            h.retranslate()
        self.lang_btn.setText(f"{i18n.lang.upper()}  ▾")
        self.gear.setToolTip(tr("settings"))
        self.reload()

    # ----------------------------------------------------------- content
    def _section(self, key):
        lb = QLabel(tr(key))
        lb.setObjectName("section")
        return lb

    def _empty(self, searching):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(10)
        ic = QLabel()
        ic.setPixmap(pixmap("clip", "#c9cad3", 32))
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFixedSize(72, 72)
        ic.setStyleSheet("background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);border-radius:36px")
        t = QLabel(tr("noresult_title" if searching else "empty_title"))
        t.setStyleSheet("font-size:17px;font-weight:600")
        b = QLabel(tr("noresult_body" if searching else "empty_body"))
        b.setObjectName("muted")
        b.setWordWrap(True)
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for x, a in ((ic, Qt.AlignmentFlag.AlignHCenter), (t, Qt.AlignmentFlag.AlignHCenter),
                     (b, Qt.AlignmentFlag.AlignHCenter)):
            v.addWidget(x, 0, a)
        return w

    def reload(self, animate=False, keep_id=None):
        self.rows = []
        clear_layout(self.lay)
        q = self.search.text().strip()
        items = self.db.list(self.filter, q)
        if not items:
            self.hl.hide()
            self.lay.addStretch(1)
            self.lay.addWidget(self._empty(bool(q)))
            self.lay.addStretch(1)
            return

        def add(it):
            r = ItemRow(it)
            r.activated.connect(self.chosen)
            r.pin_toggled.connect(self._pin)
            r.hovered.connect(self._hover)
            self.rows.append(r)
            self.lay.addWidget(r)

        if self.filter == "all" and not q:
            pinned = [i for i in items if i["pinned"]]
            recent = [i for i in items if not i["pinned"]]
            if pinned:
                self.lay.addWidget(self._section("sec_pinned"))
                for i in pinned:
                    add(i)
            if recent:
                self.lay.addWidget(self._section("sec_recent"))
                for i in recent:
                    add(i)
        else:
            for i in items:
                add(i)
        self.lay.addStretch(1)
        self.hl.show()
        self.hl.lower()
        self.sel = next((n for n, r in enumerate(self.rows) if r.item_id == keep_id), 0)
        QTimer.singleShot(0, lambda: self._select(self.sel, animate=False))
        if animate and winutil.animations_enabled():
            self._stagger()

    def _stagger(self):
        for n, row in enumerate(self.rows[:7]):
            eff = QGraphicsOpacityEffect(row)
            eff.setOpacity(0.0)
            row.setGraphicsEffect(eff)
            an = QPropertyAnimation(eff, b"opacity", row)
            an.setDuration(220)
            an.setStartValue(0.0)
            an.setEndValue(1.0)
            an.setEasingCurve(EASE_OUT)
            an.finished.connect(lambda r=row: r.setGraphicsEffect(None))
            QTimer.singleShot(40 + n * 30, an.start)

    # --------------------------------------------------------- selection
    def _select(self, idx, animate=True):
        if not self.rows:
            return
        self.sel = max(0, min(idx, len(self.rows) - 1))
        row = self.rows[self.sel]
        self.scroll.ensureWidgetVisible(row, 0, 24)
        rect = row.geometry()
        if animate and self.hl.isVisible() and winutil.animations_enabled():
            an = QPropertyAnimation(self.hl, b"geometry", self.hl)
            an.setDuration(150)
            an.setStartValue(self.hl.geometry())
            an.setEndValue(rect)
            an.setEasingCurve(EASE_IN_OUT)
            an.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        else:
            self.hl.setGeometry(rect)

    def _hover(self, row):
        if row in self.rows and self.rows.index(row) != self.sel:
            self._select(self.rows.index(row))

    def _set_filter(self, key):
        self.filter = key
        self.tabs[key].setChecked(True)
        self.reload()

    def _pin(self, item_id):
        row = self.db.get(item_id)
        if row:
            self.db.set_pinned(item_id, not row["pinned"])
            self.reload(keep_id=item_id)

    def _activate_selected(self):
        if self.rows:
            self.chosen.emit(self.rows[self.sel].item_id)

    def _delete_selected(self):
        if self.rows:
            idx = self.sel
            self.db.delete(self.rows[idx].item_id)
            self.reload()
            self.sel = min(idx, len(self.rows) - 1)
            QTimer.singleShot(0, lambda: self._select(self.sel, animate=False))

    # ---------------------------------------------------------- language
    def _lang_menu(self):
        menu = QMenu(self)
        for code, key in (("auto", "lang_auto"), ("en", "lang_en"), ("id", "lang_id")):
            act = menu.addAction(tr(key))
            act.setCheckable(True)
            act.setChecked(i18n.pref == code)
            act.setData(code)
        self._menu_open = True
        act = menu.exec(self.lang_btn.mapToGlobal(QPoint(0, self.lang_btn.height() + 4)))
        self._menu_open = False
        self.activateWindow()
        if act is not None:
            self.language_chosen.emit(act.data())

    # ---------------------------------------------------- show / events
    def open_at_cursor(self):
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.filter = "all"
        self.tabs["all"].setChecked(True)
        self.reload(animate=True)
        pos = QCursor.pos()
        scr = QGuiApplication.screenAt(pos) or QGuiApplication.primaryScreen()
        g = scr.availableGeometry()
        x = min(max(pos.x() - 40, g.left() + 8), g.right() - self.width() - 8)
        y = min(max(pos.y() + 16, g.top() + 8), g.bottom() - self.height() - 8)
        self._opened_at = time.monotonic()
        self.show_animated(QPoint(x, y))
        winutil.force_foreground(int(self.winId()))
        self.search.setFocus()

    def eventFilter(self, obj, ev):
        if obj is self.search and ev.type() == QEvent.Type.KeyPress:
            k = ev.key()
            if k == Qt.Key.Key_Down:
                self._select(self.sel + 1)
                return True
            if k == Qt.Key.Key_Up:
                self._select(self.sel - 1)
                return True
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._activate_selected()
                return True
            if k == Qt.Key.Key_Escape:
                self.hide_animated()
                return True
            if k == Qt.Key.Key_Delete and not self.search.text():
                self._delete_selected()
                return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide_animated()
        else:
            super().keyPressEvent(e)

    def changeEvent(self, e):
        if (e.type() == QEvent.Type.ActivationChange and self.isVisible() and not self.isActiveWindow()
                and not self._menu_open and QApplication.activePopupWidget() is None
                and time.monotonic() - self._opened_at > 0.35):
            QTimer.singleShot(0, self.hide_animated)
        super().changeEvent(e)
