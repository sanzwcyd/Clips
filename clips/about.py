from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from . import __version__
from .i18n import i18n, tr
from .paths import resource
from .theme import GlassWindow, HLine, TitleBar

LINKS = {
    "Instagram": "https://www.instagram.com/sanz.arw/",
    "X": "https://x.com/LineBezier",
    "GitHub": "https://github.com/sanzwcyd",
    "Saweria": "https://saweria.co/sanzwcyd",
}
CREDIT = "sanz & clawd"


class Bubble(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(250, 50)
        self.text = ""

    def set_text(self, t):
        self.text = t
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(255, 255, 255, 40))
        p.setPen(QPen(QColor(255, 255, 255, 70), 1))
        p.drawRoundedRect(QRectF(.5, .5, self.width() - 1, 38), 14, 14)
        x = self.width() - 54
        p.drawPolygon(QPolygonF([QPointF(x, 38), QPointF(x + 16, 38), QPointF(x + 8, 49)]))
        p.setPen(QColor("#F2F3F7"))
        f = self.font()
        f.setPixelSize(14)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, self.width(), 38), Qt.AlignmentFlag.AlignCenter, self.text)


class Clawd(QWidget):
    """Pixel mascot, waving."""
    BODY, EYE = QColor("#D97757"), QColor("#1C1D22")

    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 162)
        self._t = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.5, 1.0)
        self.anim.setEndValue(0.0)
        self.anim.setDuration(1200)
        self.anim.setLoopCount(-1)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.valueChanged.connect(self._tick)

    def _tick(self, v):
        self._t = float(v)
        self.update()

    def showEvent(self, e):
        self.anim.start()

    def hideEvent(self, e):
        self.anim.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(1.25, 1.25)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.BODY)
        for r in ((30, 30, 100, 60), (10, 55, 20, 18), (130, 55, 20, 14),
                  (40, 90, 12, 22), (62, 90, 12, 22), (86, 90, 12, 22), (108, 90, 12, 22)):
            p.drawRect(*r)
        p.save()
        p.translate(146, 60)
        p.rotate(-14 + 28 * self._t)
        p.drawRect(-6, -40, 12, 42)
        p.restore()
        p.setBrush(self.EYE)
        p.drawRect(52, 48, 10, 18)
        p.drawRect(98, 48, 10, 18)


class AboutWindow(GlassWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 620)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.title = TitleBar("about", self)
        root.addWidget(self.title)

        body = QVBoxLayout()
        body.setContentsMargins(32, 22, 32, 0)
        body.setSpacing(0)
        self.bubble = Bubble()
        body.addWidget(self.bubble, 0, Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(Clawd(), 0, Qt.AlignmentFlag.AlignHCenter)
        body.addSpacing(14)
        name = QHBoxLayout()
        name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = QLabel()
        logo.setPixmap(QPixmap(resource("assets/icon.png")).scaled(
            32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title = QLabel("Clips")
        title.setStyleSheet("font-size:22px;font-weight:600;color:#F2F3F7")
        name.addWidget(logo)
        name.addSpacing(8)
        name.addWidget(title)
        body.addLayout(name)
        self.version = QLabel()
        self.version.setObjectName("muted")
        body.addSpacing(4)
        body.addWidget(self.version, 0, Qt.AlignmentFlag.AlignHCenter)
        body.addSpacing(18)
        body.addWidget(HLine())
        body.addSpacing(16)
        self.made_by = QLabel()
        self.made_by.setObjectName("muted")
        who = QLabel(CREDIT)
        who.setStyleSheet("font-size:15px;font-weight:600")
        body.addWidget(self.made_by, 0, Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(who, 0, Qt.AlignmentFlag.AlignHCenter)
        body.addStretch(1)
        root.addLayout(body, 1)

        links = QHBoxLayout()
        links.setContentsMargins(24, 0, 24, 0)
        links.setSpacing(8)
        for label, url in LINKS.items():
            b = QPushButton(label)
            b.setObjectName("ghost")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(40)
            b.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            links.addWidget(b)
        root.addLayout(links)
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("primary")
        self.close_btn.clicked.connect(lambda: self.hide_animated())
        row = QHBoxLayout()
        row.setContentsMargins(0, 16, 0, 20)
        row.addStretch()
        row.addWidget(self.close_btn)
        row.addStretch()
        root.addLayout(row)

        i18n.changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self):
        self.bubble.set_text(tr("about_hi"))
        self.version.setText(tr("version", v=__version__))
        self.made_by.setText(tr("made_by"))
        self.close_btn.setText(tr("close"))
        self.title.retranslate()
