"""Shift+悬停调试工具 — 按住 Shift 显示鼠标下方控件的类型/尺寸/父级链."""

from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QEvent, QTimer, QRect, QPoint, QSize


class DebugOverlay(QLabel):
    """Semi-transparent overlay showing widget info on Shift+hover."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 210);
                color: #0f0;
                font-family: Consolas, monospace;
                font-size: 10px;
                padding: 6px 8px;
                border: 1px solid #0f0;
                border-radius: 3px;
            }
        """)
        self.setVisible(False)
        self._shift_held = False
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._refresh)

    def install(self, app: QApplication):
        """Install event filter and start monitoring."""
        app.installEventFilter(self)
        self._timer.start()
        self.show()  # needed for overlay window
        self.setVisible(False)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Shift:
            self._shift_held = True
        elif event.type() == QEvent.Type.KeyRelease and event.key() == Qt.Key.Key_Shift:
            self._shift_held = False
            self.setVisible(False)
        return False  # never consume events

    def _refresh(self):
        if not self._shift_held:
            return

        pos = QApplication.instance().screens()[0].cursor().pos()  # screen coords
        widget = QApplication.widgetAt(pos)
        if widget is None:
            self.setVisible(False)
            return

        # Collect widget info
        lines = []
        w = widget

        # Class & object name
        cls = type(w).__name__
        oname = w.objectName() or "(无名)"
        lines.append(f"{cls}  [{oname}]")

        # Geometry
        geo = w.geometry()
        lines.append(f"  x={geo.x()} y={geo.y()} w={geo.width()} h={geo.height()}")

        # Layout margins
        layout = w.layout()
        if layout:
            m = layout.contentsMargins()
            lines.append(f"  布局边距: L={m.left()} T={m.top()} R={m.right()} B={m.bottom()}")

        # Size policy & fixed size
        sp_h = w.sizePolicy().horizontalPolicy()
        sp_v = w.sizePolicy().verticalPolicy()
        sp_map = {0: "Fixed", 1: "Minimum", 3: "MinimumExpanding", 4: "Preferred", 5: "Expanding", 7: "Ignored"}
        lines.append(f"  sizePolicy: H={sp_map.get(sp_h, str(sp_h))} V={sp_map.get(sp_v, str(sp_v))}")

        mh = w.minimumHeight()
        mxh = w.maximumHeight()
        fh = w.minimumHeight() if w.minimumHeight() == w.maximumHeight() else None
        if fh and fh < 16777215:
            lines.append(f"  fixedHeight={fh}")

        # Stylesheet snippet
        ss = w.styleSheet()
        if ss:
            short = ss[:120].replace('\n', ' ')
            lines.append(f"  style: {short}...")

        # Parent chain (up to 4 levels)
        lines.append("  父级链:")
        parent = w.parentWidget()
        depth = 0
        while parent and depth < 4:
            indent = "    " + "  " * depth
            p_cls = type(parent).__name__
            p_name = parent.objectName() or ""
            p_geo = parent.geometry()
            p_m = parent.layout().contentsMargins() if parent.layout() else None
            margin_str = f" layoutMgn=({p_m.left()},{p_m.top()},{p_m.right()},{p_m.bottom()})" if p_m else ""
            lines.append(f"{indent}↳ {p_cls} [{p_name}] xy=({p_geo.x()},{p_geo.y()}) sz=({p_geo.width()}x{p_geo.height()}){margin_str}")
            parent = parent.parentWidget()
            depth += 1

        self.setText('\n'.join(lines))
        self.adjustSize()

        # Position overlay near cursor but inside screen
        sx = pos.x() + 20
        sy = pos.y() + 20
        screen = QApplication.instance().screens()[0].geometry()
        if sx + self.width() > screen.right():
            sx = pos.x() - self.width() - 20
        if sy + self.height() > screen.bottom():
            sy = pos.y() - self.height() - 20
        self.move(sx, sy)
        self.setVisible(True)


def install_debug_overlay(app: QApplication) -> DebugOverlay:
    """Create and install the debug overlay.

    Usage in app.py:
        overlay = install_debug_overlay(app)
        # Press Shift and hover over any widget to debug.

    Returns the overlay instance for later removal if needed.
    """
    overlay = DebugOverlay()
    overlay.install(app)
    return overlay
