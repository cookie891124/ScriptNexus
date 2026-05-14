"""Shift+悬停调试 — 按住 Shift 在鼠标旁显示控件诊断信息."""

import time
from PyQt6.QtWidgets import QApplication, QToolTip, QWidget
from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtGui import QCursor


def _build_info(widget: QWidget) -> str:
    """Build plain-text diagnostic info for a widget."""
    lines = []
    cls = type(widget).__name__
    oname = widget.objectName() or "( )"
    lines.append(f"{cls} [{oname}]")
    geo = widget.geometry()
    lines.append(f"  xy=({geo.x()},{geo.y()}) sz={geo.width()}x{geo.height()}")

    lay = widget.layout()
    if lay:
        m = lay.contentsMargins()
        lines.append(f"  layoutMargins: L{m.left()} T{m.top()} R{m.right()} B{m.bottom()}")
        lines.append(f"  layoutSpacing: {lay.spacing()}  children: {lay.count()}")

    mnh = widget.minimumHeight()
    mxh = widget.maximumHeight()
    if mnh == mxh and mnh < 16777215:
        lines.append(f"  >>> FIXED height={mnh} <<<")
    else:
        lines.append(f"  minH={mnh}  maxH={mxh}")

    sp = widget.sizePolicy()
    sn = {0: "Fixed", 1: "Min", 3: "MinExp", 4: "Pref", 5: "Exp", 7: "Ignore"}
    lines.append(f"  sizePolicy: H={sn.get(sp.horizontalPolicy(),'?')} V={sn.get(sp.verticalPolicy(),'?')}")

    ss = widget.styleSheet()
    if ss:
        lines.append(f"  QSS: {ss[:120].replace(chr(10),' ')}")

    lines.append("Parent chain:")
    p = widget.parentWidget()
    d = 0
    while p and d < 4:
        pc = type(p).__name__
        pn = p.objectName() or ""
        pg = p.geometry()
        ss = p.styleSheet()
        pl = p.layout()
        pm = f" LM({pl.contentsMargins().left()},{pl.contentsMargins().top()},{pl.contentsMargins().right()},{pl.contentsMargins().bottom()})" if pl else ""
        sc = f" QSS={ss[:60].replace(chr(10),'')}" if ss else ""
        lines.append(f"  {'  '*d}{pc}[{pn}] xy({pg.x()},{pg.y()}) {pg.width()}x{pg.height()}{pm}{sc}")
        p = p.parentWidget()
        d += 1

    return '\n'.join(lines)


class _DebugFilter(QObject):
    """Global event filter with debounced Shift+hover diagnostic."""

    def __init__(self):
        super().__init__()
        self._last_widget_id = None
        self._last_show = 0

    def eventFilter(self, obj, event):
        if event.type() not in (QEvent.Type.MouseMove, QEvent.Type.KeyRelease):
            return False

        # On Shift release, hide immediately
        if event.type() == QEvent.Type.KeyRelease:
            if event.key() == Qt.Key.Key_Shift:
                QToolTip.hideText()
                self._last_widget_id = None
            return False

        # MouseMove: check Shift
        mods = QApplication.queryKeyboardModifiers()
        if not (mods & Qt.KeyboardModifier.ShiftModifier):
            QToolTip.hideText()
            self._last_widget_id = None
            return False

        # Debounce: max one update per 250ms, only if widget changed
        now = time.time()
        if now - self._last_show < 0.25:
            return False

        pos = QCursor.pos()
        widget = QApplication.widgetAt(pos)
        if widget is None:
            return False

        wid = id(widget)
        if wid == self._last_widget_id:
            return False

        self._last_widget_id = wid
        self._last_show = now
        QToolTip.showText(pos, _build_info(widget))
        return False


def install_debug_overlay(app: QApplication):
    f = _DebugFilter()
    app.installEventFilter(f)
    app._debug_filter = f
