import functools

from PySide6.QtCore import (QByteArray, QEasingCurve, QObject, QParallelAnimationGroup, QPoint,
                            QPointF, QPropertyAnimation, QRectF, QSize, Qt, Signal, Property)
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPainterPath, QPen, QPixmap, QFontMetrics
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QAbstractButton, QHBoxLayout, QLabel, QToolButton, QWidget

from . import winutil
from .i18n import tr


# ------------------------------------------------------------------ easing
def bezier(x1, y1, x2, y2) -> QEasingCurve:
    c = QEasingCurve(QEasingCurve.Type.BezierSpline)
    c.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))
    return c


EASE_OUT = bezier(.16, 1, .3, 1)     # things appearing: fast start, soft landing
EASE_IN = bezier(.4, 0, 1, 1)        # things leaving
EASE_IN_OUT = bezier(.4, 0, .2, 1)   # things moving / toggling


# ------------------------------------------------------------------ accent
class Theme(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.accent = QColor("#3EC9A7")

    def set_accent(self, hex_color: str):
        c = QColor(hex_color)
        for _ in range(6):  # keep the accent readable on the dark glass
            if c.lightnessF() >= 0.45:
                break
            c = c.lighter(125)
        if c != self.accent:
            self.accent = c
            self.changed.emit()

    @property
    def on_accent(self) -> str:
        return "#0E1A17" if self.accent.lightnessF() > 0.5 else "#FFFFFF"


theme = Theme()


def build_qss() -> str:
    a, on = theme.accent.name(), theme.on_accent
    hover = theme.accent.lighter(112).name()
    return f"""
QWidget{{color:#e8e9ee;font-family:"Segoe UI Variable Text","Segoe UI",sans-serif;font-size:14px}}
QLabel{{background:transparent}}
QLabel#muted{{color:#b4b6c2;font-size:12px}}
QLabel#section{{color:#b4b6c2;font-size:11px;font-weight:600;letter-spacing:1px;padding:14px 12px 4px 12px}}
QLabel#kbd{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:5px;
  padding:1px 6px;font-size:11px;font-weight:600;color:#e1e2ea}}
QFrame#divider{{background:rgba(255,255,255,.14);max-height:1px;min-height:1px;border:0}}
QLineEdit#search{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:10px;
  padding:0 14px;min-height:42px;selection-background-color:{a};selection-color:{on}}}
QLineEdit#search:focus{{border:1px solid {a}}}
QLineEdit{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:8px;padding:6px 10px}}
QPushButton[chip="true"]{{background:rgba(255,255,255,.1);color:#e1e2ea;border:0;border-radius:16px;padding:0 14px;
  min-height:32px;font-weight:600;font-size:13px}}
QPushButton[chip="true"]:hover{{background:rgba(255,255,255,.16)}}
QPushButton[chip="true"]:checked{{background:{a};color:{on}}}
QPushButton#primary{{background:{a};color:{on};border:0;border-radius:10px;padding:0 28px;min-height:40px;font-weight:600}}
QPushButton#primary:hover{{background:{hover}}}
QPushButton#ghost{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.22);border-radius:8px;
  padding:0 14px;min-height:34px;font-weight:600;font-size:13px}}
QPushButton#ghost:hover{{background:rgba(255,255,255,.16)}}
QPushButton#ghost:disabled{{color:#7d7f8b}}
QToolButton#icon{{background:transparent;border:0;border-radius:8px}}
QToolButton#icon:hover{{background:rgba(255,255,255,.12)}}
QToolButton#lang{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:10px;
  padding:0 12px;font-weight:600;font-size:13px}}
QToolButton#lang:hover{{background:rgba(255,255,255,.14)}}
#hl{{background:rgba(255,255,255,.14);border-left:3px solid {a};border-radius:8px}}
QComboBox{{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:8px;
  padding:0 12px;min-height:34px;font-weight:600;font-size:13px}}
QComboBox:hover{{background:rgba(255,255,255,.14)}}
QComboBox::drop-down{{border:0;width:22px}}
QComboBox QAbstractItemView{{background:#1c1d24;border:1px solid rgba(255,255,255,.2);selection-background-color:rgba(255,255,255,.16);
  outline:0;padding:4px}}
QMenu{{background:rgba(24,25,32,.78);border:1px solid rgba(255,255,255,.2);border-radius:12px;padding:6px}}
QMenu::item{{padding:9px 14px 9px 12px;border-radius:8px;min-width:200px}}
QMenu::item:selected{{background:rgba(255,255,255,.14)}}
QMenu::separator{{height:1px;background:rgba(255,255,255,.14);margin:4px 8px}}
QScrollArea{{background:transparent;border:0}}
QScrollArea>QWidget>QWidget{{background:transparent}}
QScrollBar:vertical{{background:transparent;width:8px;margin:2px}}
QScrollBar::handle:vertical{{background:rgba(255,255,255,.25);border-radius:3px;min-height:30px}}
QScrollBar::handle:vertical:hover{{background:rgba(255,255,255,.4)}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0}}
QDialog,QMessageBox{{background:#1c1d24}}
QDialog QPushButton{{background:rgba(255,255,255,.1);color:#e8e9ee;border:1px solid rgba(255,255,255,.22);border-radius:8px;
  padding:0 18px;min-height:34px;min-width:72px;font-weight:600;font-size:13px}}
QDialog QPushButton:hover{{background:rgba(255,255,255,.18)}}
QDialog QPushButton:default{{background:{a};color:{on};border:0}}
QDialog QPushButton:default:hover{{background:{hover}}}
QListWidget{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.14);border-radius:8px;padding:4px}}
QListWidget::item{{padding:6px;border-radius:6px}}
QListWidget::item:selected{{background:rgba(255,255,255,.16)}}
QToolTip{{background:#25262c;color:#e8e9ee;border:1px solid rgba(255,255,255,.2);padding:4px}}
"""


# ------------------------------------------------------------------- icons
ICONS = {
    "text": '<path d="M4 6h16M4 12h16M4 18h10"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "pin": '<path d="M12 17v5M9 3h6l-1 6 4 4H6l4-4z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.4-2.3 1a7 7 0 0 0-2-1.2L14.2 3h-4l-.4 2.7a7 7 0 0 0-2 1.2l-2.3-1-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.3-1a7 7 0 0 0 2 1.2l.4 2.7h4l.4-2.7a7 7 0 0 0 2-1.2l2.3 1 2-3.4-2-1.5c.1-.4.1-.8.1-1.2z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>',
    "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "eyeoff": '<path d="M3 3l18 18M10.6 6.2A9.6 9.6 0 0 1 12 6c6 0 10 6 10 6a17 17 0 0 1-3.2 3.7M6.6 6.7A17 17 0 0 0 2 12s4 7 10 7c1.7 0 3.2-.4 4.5-1M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.01"/>',
    "close": '<path d="M5 5l14 14M19 5L5 19"/>',
    "power": '<path d="M12 3v9M6.5 6.5a8 8 0 1 0 11 0"/>',
    "clip": '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4V3h6v1M9 10h6M9 14h4"/>',
}


@functools.lru_cache(maxsize=None)
def pixmap(name: str, color: str = "#c9cad3", size: int = 18, fill: str = "none") -> QPixmap:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" '
           f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def icon(name, color="#c9cad3", size=18, fill="none") -> QIcon:
    return QIcon(pixmap(name, color, size, fill))


# ----------------------------------------------------------------- widgets
class IconButton(QToolButton):
    def __init__(self, name, size=40, icon_size=18, parent=None):
        super().__init__(parent)
        self.setObjectName("icon")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(size, size)
        self.setIconSize(QSize(icon_size, icon_size))
        self.set_icon(name)

    def set_icon(self, name, color="#c9cad3", fill="none"):
        self.setIcon(icon(name, color, self.iconSize().width(), fill))


class ElidedLabel(QWidget):
    def __init__(self, text="", color="#e8e9ee", pixel_size=14, bold=False, spacing=0.0):
        super().__init__()
        self._text, self._color = text, QColor(color)
        f = self.font()
        f.setPixelSize(pixel_size)
        f.setBold(bold)
        f.setLetterSpacing(QFont_Absolute, spacing)
        self.setFont(f)
        self.setMinimumWidth(0)
        self.setFixedHeight(QFontMetrics(f).height() + 2)

    def setText(self, t):
        self._text = t
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(self._color)
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   QFontMetrics(self.font()).elidedText(self._text, Qt.TextElideMode.ElideRight, self.width()))


from PySide6.QtGui import QFont  # noqa: E402
QFont_Absolute = QFont.SpacingType.AbsoluteSpacing


class ToggleSwitch(QAbstractButton):
    def __init__(self, checked=False):
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(44, 24)
        self._t = 1.0 if checked else 0.0
        self.setChecked(checked)
        self._anim = QPropertyAnimation(self, b"t", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(EASE_IN_OUT)
        self.toggled.connect(self._animate)
        theme.changed.connect(self.update)

    def _animate(self, on):
        self._anim.stop()
        if winutil.animations_enabled():
            self._anim.setStartValue(self._t)
            self._anim.setEndValue(1.0 if on else 0.0)
            self._anim.start()
        else:
            self._t = 1.0 if on else 0.0
            self.update()

    def set_silently(self, on):
        self.blockSignals(True)
        self.setChecked(on)
        self.blockSignals(False)
        self._anim.stop()
        self._t = 1.0 if on else 0.0
        self.update()

    def _get_t(self):
        return self._t

    def _set_t(self, v):
        self._t = v
        self.update()

    t = Property(float, _get_t, _set_t)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        off, on = QColor(255, 255, 255, 56), theme.accent
        mix = QColor(int(off.red() + (on.red() - off.red()) * self._t),
                     int(off.green() + (on.green() - off.green()) * self._t),
                     int(off.blue() + (on.blue() - off.blue()) * self._t),
                     int(off.alpha() + (255 - off.alpha()) * self._t))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(mix)
        p.drawRoundedRect(QRectF(0, 0, 44, 24), 12, 12)
        p.setBrush(QColor("#0E1A17") if self._t > 0.5 and theme.on_accent != "#FFFFFF" else QColor("#F2F3F7"))
        p.drawEllipse(QRectF(2 + 20 * self._t, 2, 20, 20))


class HLine(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(1)

    def paintEvent(self, _):
        QPainter(self).fillRect(self.rect(), QColor(255, 255, 255, 36))


RADIUS = 16


class GlassWindow(QWidget):
    """Frameless frosted-glass window.

    Instead of relying on Windows' acrylic (which turns see-through when a window is
    inactive), we take a snapshot of the screen behind the window right before it
    appears, blur it, darken it, and paint that as the background. Result: always
    blurred, never too transparent. Show/hide use eased animations."""

    TINT = QColor(22, 23, 30, 150)

    def __init__(self, popup=False, no_focus=False):
        flags = Qt.WindowType.FramelessWindowHint
        flags |= (Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint) if popup else Qt.WindowType.Window
        if no_focus:
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        if no_focus:
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._anim, self._closing = None, False
        self._bg, self._bg_origin = None, QPoint()

    # ---------------------------------------------------------- backdrop
    def _grab_screen(self, center):
        scr = QGuiApplication.screenAt(center) or QGuiApplication.primaryScreen()
        return scr.grabWindow(0), scr.geometry().topLeft()

    def _capture_backdrop(self, center):
        try:
            pm, origin = self._grab_screen(center)
        except Exception:
            pm = None
        if pm is None or pm.isNull():
            self._bg = None
            return
        dpr, img = pm.devicePixelRatio(), pm.toImage()
        w, h = img.width(), img.height()
        smooth = (Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        tiny = img.scaled(max(2, w // 24), max(2, h // 24), *smooth)      # throw away detail
        mid = tiny.scaled(max(2, w // 6), max(2, h // 6), *smooth)        # grow back softly
        big = mid.scaled(w, h, *smooth)
        self._bg = QPixmap.fromImage(big)
        self._bg.setDevicePixelRatio(dpr)
        self._bg_origin = origin

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(.5, .5, -.5, -.5), RADIUS, RADIUS)
        p.setClipPath(path)
        if self._bg is not None:
            g = self.mapToGlobal(QPoint(0, 0))  # keeps the backdrop aligned if the window is dragged
            p.drawPixmap(QPointF(self._bg_origin.x() - g.x(), self._bg_origin.y() - g.y()), self._bg)
            p.fillPath(path, self.TINT)
        else:
            p.fillPath(path, QColor(26, 27, 34, 240))
        p.setClipping(False)
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    # --------------------------------------------------------- animation
    def _stop(self):
        if self._anim is not None:
            self._anim.stop()
            self._anim = None

    def show_animated(self, pos=None, offset=QPoint(0, 12), activate=True):
        self._stop()
        self._closing = False
        if pos is not None:
            self.move(pos)
        end = self.pos()
        if not self.isVisible():
            self._capture_backdrop(end + QPoint(self.width() // 2, self.height() // 2))
        anim_on = winutil.animations_enabled()
        self.setWindowOpacity(0.0 if anim_on else 1.0)
        if anim_on:
            self.move(end + offset)
        self.show()
        if activate:
            self.raise_()
            self.activateWindow()
        if not anim_on:
            return
        g = QParallelAnimationGroup(self)
        for prop, a, b in ((b"windowOpacity", 0.0, 1.0), (b"pos", end + offset, end)):
            an = QPropertyAnimation(self, prop)
            an.setDuration(180)
            an.setStartValue(a)
            an.setEndValue(b)
            an.setEasingCurve(EASE_OUT)
            g.addAnimation(an)
        self._anim = g
        g.start()

    def hide_animated(self, *_ignored, offset=QPoint(0, 8)):
        """*_ignored swallows the 'checked' bool that button clicked-signals pass in."""
        if not self.isVisible() or self._closing:
            return
        self._stop()
        if not winutil.animations_enabled():
            self.hide()
            return
        self._closing = True
        start = self.pos()
        g = QParallelAnimationGroup(self)
        for prop, a, b in ((b"windowOpacity", 1.0, 0.0), (b"pos", start, start + offset)):
            an = QPropertyAnimation(self, prop)
            an.setDuration(120)
            an.setStartValue(a)
            an.setEndValue(b)
            an.setEasingCurve(EASE_IN)
            g.addAnimation(an)

        def done():
            self.hide()
            self.move(start)
            self.setWindowOpacity(1.0)
            self._closing = False

        g.finished.connect(done)
        self._anim = g
        g.start()


class TitleBar(QWidget):
    def __init__(self, key, win):
        super().__init__(win)
        self.key, self.win = key, win
        self.setFixedHeight(44)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 4, 0)
        self.label = QLabel()
        self.label.setStyleSheet("font-size:13px;font-weight:600;color:#e1e2ea")
        self.close_btn = IconButton("close", 44, 14)
        self.close_btn.clicked.connect(lambda: win.hide_animated())
        lay.addWidget(self.label)
        lay.addStretch()
        lay.addWidget(self.close_btn)
        self.retranslate()

    def retranslate(self):
        self.label.setText(tr(self.key))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.win.windowHandle():
            self.win.windowHandle().startSystemMove()

    def paintEvent(self, _):
        QPainter(self).fillRect(0, self.height() - 1, self.width(), 1, QColor(255, 255, 255, 36))


def clear_layout(layout):
    """Remove and dispose every widget in a layout immediately (no ghost widgets)."""
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w is not None:
            w.hide()
            w.setParent(None)
            w.deleteLater()
        elif it.layout() is not None:
            clear_layout(it.layout())
