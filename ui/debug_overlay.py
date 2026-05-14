"""Shift+悬停调试工具 — 按住 Shift 显示鼠标下方控件的类型/尺寸/父级链."""

from PyQt6.QtWidgets import QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor


class DebugOverlay:
    """Shift+hover widget diagnostic overlay.

    Holds Shift → every 300ms reads cursor position, finds widget under
    cursor, shows a green floating tooltip with widget class/geometry/
    margins/layout/parent chain. Release Shift → hide.
    """

    def __init__(self, app: QApplication):
        self._app = app
        self._label = QLabel()
        self._label.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._label.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 220);
                color: #00ff00;
                font-family: Consolas, monospace;
                font-size: 10px;
                padding: 6px 8px;
                border: 1px solid #00ff00;
                border-radius: 3px;
            }
        """)
        self._label.hide()

        self._timer = QTimer()
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        # Check Shift state each tick (no event filter needed)
        modifiers = QApplication.queryKeyboardModifiers()
        if not (modifiers & Qt.KeyboardModifier.ShiftModifier):
            if self._label.isVisible():
                self._label.hide()
            return

        pos = QCursor.pos()  # global screen coords
        widget = QApplication.widgetAt(pos)
        if widget is None:
            self._label.hide()
            return

        # Build info lines
        lines = []
        w = widget
        cls = type(w).__name__
        oname = w.objectName() or "(无)"
        lines.append(f"{cls}  [{oname}]")
        geo = w.geometry()
        lines.append(f"  x={geo.x()} y={geo.y()} w={geo.width()} h={geo.height()}")

        layout = w.layout()
        if layout:
            m = layout.contentsMargins()
            lines.append(f"  layoutMargins: L{m.left()} T{m.top()} R{m.right()} B{m.bottom()}")
            lines.append(f"  layoutSpacing: {layout.spacing()}")
            cnt = layout.count()
            lines.append(f"  layoutChildren: {cnt}")

        # Size constraints
        mnh = w.minimumHeight()
        mxh = w.maximumHeight()
        if mnh > 0:
            lines.append(f"  minHeight={mnh}")
        if mxh < 16777215:
            lines.append(f"  maxHeight={mxh}")
        if mnh == mxh and mnh < 16777215:
            lines.append(f"  >>> FIXED height={mnh} <<<")

        # sizePolicy
        sp = w.sizePolicy()
        sp_names = {0: "Fixed", 1: "Minimum", 3: "MinExpanding", 4: "Preferred", 5: "Expanding", 7: "Ignored"}
        lines.append(f"  sizePolicy: H={sp_names.get(sp.horizontalPolicy(), '?')} V={sp_names.get(sp.verticalPolicy(), '?')}")

        # StyleSheet snippet
        ss = w.styleSheet()
        if ss:
            short = ss[:100].replace('\n', ' ').replace('\t', ' ')
            lines.append(f"  QSS: {short}")

        # Parent chain (3 levels)
        lines.append("  父级链:")
        p = w.parentWidget()
        d = 0
        while p and d < 3:
            pad = "  " * d
            pc = type(p).__name__
            pn = p.objectName() or ""
            pg = p.geometry()
            pl = p.layout()
            pm = f" LM=({pl.contentsMargins().left()},{pl.contentsMargins().top()},{pl.contentsMargins().right()},{pl.contentsMargins().bottom()})" if pl else ""
            lines.append(f"{pad}↳ {pc} [{pn}] xy=({pg.x()},{pg.y()}) sz=({pg.width()}x{pg.height()}){pm}")
            p = p.parentWidget()
            d += 1

        self._label.setText('\n'.join(lines))
        self._label.adjustSize()

        # Position near cursor, avoid screen edges
        sx = pos.x() + 20
        sy = pos.y() + 20
        screen = self._app.primaryScreen().availableGeometry()
        if sx + self._label.width() > screen.right():
            sx = pos.x() - self._label.width() - 10
        if sy + self._label.height() > screen.bottom():
            sy = pos.y() - self._label.height() - 10
        self._label.move(sx, sy)
        self._label.show()
        self._label.raise_()


def install_debug_overlay(app: QApplication) -> DebugOverlay:
    """Create and start the Shift+hover debug overlay."""
    return DebugOverlay(app)
