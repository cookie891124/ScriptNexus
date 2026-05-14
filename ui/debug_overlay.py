"""Shift+悬停调试 — 按住 Shift 在鼠标旁显示控件诊断信息."""

from PyQt6.QtWidgets import QApplication, QToolTip, QWidget
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QCursor


def _build_info(widget: QWidget) -> str:
    """Build diagnostic text for a widget."""
    lines = []
    cls = type(widget).__name__
    oname = widget.objectName() or "(无)"
    lines.append(f"<b>{cls}</b> [{oname}]")
    geo = widget.geometry()
    lines.append(f"x={geo.x()} y={geo.y()} w={geo.width()} h={geo.height()}")

    lay = widget.layout()
    if lay:
        m = lay.contentsMargins()
        lines.append(f"LM L{m.left()} T{m.top()} R{m.right()} B{m.bottom()} spacing={lay.spacing()} children={lay.count()}")

    mnh = widget.minimumHeight()
    mxh = widget.maximumHeight()
    lines.append(f"minH={mnh} maxH={mxh}")
    if mnh == mxh and mnh < 16777215:
        lines.append(f"<span style='color:#ff0'>>>> FIXED h={mnh}</span>")

    sp = widget.sizePolicy()
    sn = {0: "Fixed", 1: "Minimum", 3: "MinExp", 4: "Pref", 5: "Exp", 7: "Ignore"}
    lines.append(f"SP H={sn.get(sp.horizontalPolicy(),'?')} V={sn.get(sp.verticalPolicy(),'?')}")

    ss = widget.styleSheet()
    if ss:
        lines.append(f"QSS: {ss[:120].replace(chr(10),' ')}")

    lines.append("<b>父级:</b>")
    p = widget.parentWidget()
    d = 0
    while p and d < 4:
        pc = type(p).__name__
        pn = p.objectName() or ""
        pg = p.geometry()
        pl = p.layout()
        pm = f" LM({pl.contentsMargins().left()},{pl.contentsMargins().top()},{pl.contentsMargins().right()},{pl.contentsMargins().bottom()})" if pl else ""
        lines.append(f"  {'  '*d}{pc}[{pn}] xy({pg.x()},{pg.y()}) {pg.width()}x{pg.height()}{pm}")
        p = p.parentWidget()
        d += 1

    return "<br>".join(lines)


class _DebugFilter(QObject):
    """Global event filter: on Shift+MouseMove, show widget diagnostics."""

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.MouseMove:
            return False

        mods = QApplication.queryKeyboardModifiers()
        if not (mods & Qt.KeyboardModifier.ShiftModifier):
            QToolTip.hideText()
            return False

        # Use widgetAt with the global cursor position
        pos = QCursor.pos()
        widget = QApplication.widgetAt(pos)
        if widget is None:
            return False

        QToolTip.showText(pos, _build_info(widget))
        return False  # don't consume


def install_debug_overlay(app: QApplication):
    """Install global event filter for Shift+hover debugging."""
    f = _DebugFilter()
    app.installEventFilter(f)
    # Keep reference alive
    app._debug_filter = f
