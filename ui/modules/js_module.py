"""JsModule - Chrome JS 脚本（bookmarklet）管理模块."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QComboBox, QFormLayout,
    QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsSimpleTextItem, QGraphicsPathItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QFont, QPen, QBrush, QColor, QPainter, QFontMetrics, QPainterPath,
)


# ===== Bookmark Preview =====

class BookmarkPreviewView(QGraphicsView):
    """Visual bookmark tree preview — vertical layout matching browser bookmarks."""

    # Card palette
    CARD_BG = QColor("#F8F9FA")
    CARD_BORDER = QColor("#E0E0E0")
    # Rows
    ROW_HOVER_BG = QColor("#E8F0FE")
    ROOT_TEXT = QColor("#1A1A1A")
    FOLDER_TEXT = QColor("#444746")
    BOOKMARK_TEXT = QColor("#3C4043")
    BOOKMARK_DOT = QColor("#1A73E8")
    HIGHLIGHT_BG = QColor("#D3E3FD")
    HIGHLIGHT_BORDER = QColor("#1A73E8")
    HIGHLIGHT_TEXT = QColor("#174EA6")
    # Layout constants
    CARD_MARGIN = 6          # card inset from viewport edge
    CARD_PAD_X = 10          # horizontal padding inside card
    CARD_PAD_TOP = 8         # top padding inside card
    CARD_PAD_BOTTOM = 8      # bottom padding inside card
    CARD_RADIUS = 6          # rounded corner radius
    ROW_HEIGHT = 26          # height per row
    INDENT_ROOT = 0          # root label indent
    INDENT_ITEM = 16         # direct bookmark indent
    INDENT_SUB = 30          # subfolder item indent
    DOT_SIZE = 6             # bookmark dot diameter

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._highlight_id = None
        self._hl_rects: dict = {}  # sid → QGraphicsRectItem for visibility toggle

    def clear_preview(self):
        self.scene.clear()
        self._highlight_id = None
        self._hl_rects.clear()

    def set_highlight(self, highlight_id):
        """Toggle highlight WITHOUT clearing/rebuilding the scene.

        This avoids triggering Qt layout recalculation that interferes
        with the QSplitter handle. Call this on selection changes.
        """
        if highlight_id == self._highlight_id:
            return
        if self._highlight_id is not None and self._highlight_id in self._hl_rects:
            self._hl_rects[self._highlight_id].setVisible(False)
        if highlight_id is not None and highlight_id in self._hl_rects:
            self._hl_rects[highlight_id].setVisible(True)
        self._highlight_id = highlight_id

    def _rounded_rect_path(self, x: float, y: float, w: float, h: float, r: float) -> QPainterPath:
        """Create a QPainterPath for a rounded rectangle."""
        path = QPainterPath()
        path.moveTo(x + r, y)
        path.lineTo(x + w - r, y)
        path.quadTo(x + w, y, x + w, y + r)
        path.lineTo(x + w, y + h - r)
        path.quadTo(x + w, y + h, x + w - r, y + h)
        path.lineTo(x + r, y + h)
        path.quadTo(x, y + h, x, y + h - r)
        path.lineTo(x, y + r)
        path.quadTo(x, y, x + r, y)
        path.closeSubpath()
        return path

    def show_preview(self, scripts, highlight_id=None):
        """Draw vertical tree: root folder → bookmarks, subfolders indented.

        Chrome bookmark bar is vertical, so this renders as a tree list:
          JS Scripts
            script A
            script B
            subfolder/
              script C
        """
        self.scene.clear()
        self._highlight_id = highlight_id
        self._hl_rects.clear()

        vp_w = max(self.width(), 200)

        if not scripts:
            f = QFont("Microsoft YaHei", 10)
            t = QGraphicsSimpleTextItem("No scripts")
            t.setFont(f)
            t.setBrush(QColor("#9AA0A6"))
            fm = QFontMetrics(f)
            t.setPos((vp_w - fm.horizontalAdvance("No scripts")) / 2, 20)
            self.scene.addItem(t)
            self.scene.setSceneRect(0, 0, vp_w, 60)
            return

        # Group scripts into direct items and subfolders
        direct_items: list[dict] = []
        subfolders: dict[str, list[dict]] = {}
        for s in scripts:
            key = s.get("parent_folder", "") or ""
            if key:
                subfolders.setdefault(key, []).append(s)
            else:
                direct_items.append(s)

        # Fonts
        font = QFont("Microsoft YaHei UI", 9)
        fm = QFontMetrics(font)
        bold_font = QFont("Microsoft YaHei UI", 9, QFont.Weight.Bold)
        root_font = QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold)

        # Measure all texts to determine card width
        max_text_w = QFontMetrics(root_font).horizontalAdvance("JS Scripts")
        for item in direct_items:
            tw = fm.horizontalAdvance(item.get("name", ""))
            if tw > max_text_w:
                max_text_w = tw
        for sub_name, items in subfolders.items():
            tw = QFontMetrics(bold_font).horizontalAdvance(sub_name + "/")
            if tw > max_text_w:
                max_text_w = tw
            for item in items:
                tw = fm.horizontalAdvance(item.get("name", ""))
                if tw > max_text_w:
                    max_text_w = tw

        # Card width = widest text + deepest indent + dot + gap + padding
        max_indent = self.INDENT_SUB if subfolders else self.INDENT_ITEM
        card_inner_w = max_text_w + max_indent + self.DOT_SIZE + 14
        card_w = min(card_inner_w + self.CARD_PAD_X * 2, vp_w - self.CARD_MARGIN * 2)
        content_w = card_w - self.CARD_PAD_X * 2  # usable text width inside card

        # Card position (centered or left-aligned with margin)
        card_x = self.CARD_MARGIN
        card_y = self.CARD_MARGIN

        # Build all rows first (two-pass to get final height before drawing card)
        rows: list[tuple[str, int, dict | None, bool]] = []  # (text, indent, item, is_folder)
        rows.append(("JS Scripts", self.INDENT_ROOT, None, False))

        for item in direct_items:
            rows.append((item.get("name", ""), self.INDENT_ITEM, item, False))

        for sub_name in sorted(subfolders.keys()):
            rows.append((sub_name + "/", self.INDENT_ITEM, None, True))
            for item in subfolders[sub_name]:
                rows.append((item.get("name", ""), self.INDENT_SUB, item, False))

        # Card height
        card_h = self.CARD_PAD_TOP + len(rows) * self.ROW_HEIGHT + self.CARD_PAD_BOTTOM
        total_h = card_y + card_h + self.CARD_MARGIN

        # --- Draw card background (single rounded rect, no overlap) ---
        card_path = self._rounded_rect_path(card_x, card_y, card_w, card_h, self.CARD_RADIUS)
        card_bg = QGraphicsPathItem(card_path)
        card_bg.setBrush(QBrush(self.CARD_BG))
        card_bg.setPen(QPen(self.CARD_BORDER, 1))
        card_bg.setZValue(-10)
        self.scene.addItem(card_bg)

        # --- Draw rows ---
        y = card_y + self.CARD_PAD_TOP

        for text, indent, item_data, is_folder in rows:
            sid = item_data.get("id") if item_data else None
            is_hl = highlight_id is not None and sid == highlight_id
            is_root = (indent == self.INDENT_ROOT and item_data is None)

            row_x = card_x + self.CARD_PAD_X + indent

            if is_root:
                self._draw_root_row(row_x, y, text, content_w - indent, root_font)
            elif is_folder:
                self._draw_folder_row(row_x, y, text, content_w - indent, bold_font, fm)
            else:
                self._draw_bookmark_row(
                    row_x, y, text, is_hl, sid,
                    font, fm, content_w - indent, card_x, card_w,
                )
            y += self.ROW_HEIGHT

        self.scene.setSceneRect(0, 0, vp_w, total_h)

    def _draw_root_row(self, x: float, y: float, text: str,
                       avail_w: float, font: QFont) -> None:
        """Draw the root folder header row."""
        lbl = QGraphicsSimpleTextItem(text)
        lbl.setPos(x, y + 4)
        lbl.setFont(font)
        lbl.setBrush(self.ROOT_TEXT)
        self.scene.addItem(lbl)

        # Separator line under root
        fm = QFontMetrics(font)
        line_y = y + self.ROW_HEIGHT - 2
        line = QGraphicsRectItem(x, line_y, avail_w, 1)
        line.setBrush(QBrush(QColor("#E0E0E0")))
        line.setPen(QPen(Qt.PenStyle.NoPen))
        line.setZValue(-1)
        self.scene.addItem(line)

    def _draw_folder_row(self, x: float, y: float, text: str,
                         avail_w: float, font: QFont, fm: QFontMetrics) -> None:
        """Draw a subfolder header row."""
        truncated = self._truncate(text, fm, avail_w - 4)
        lbl = QGraphicsSimpleTextItem(truncated)
        lbl.setPos(x, y + 4)
        lbl.setFont(font)
        lbl.setBrush(self.FOLDER_TEXT)
        self.scene.addItem(lbl)

    def _draw_bookmark_row(self, x: float, y: float, text: str,
                           highlighted: bool, sid,
                           font: QFont, fm: QFontMetrics,
                           avail_w: float,
                           card_x: float, card_w: float) -> None:
        """Draw a bookmark item row with dot indicator and optional highlight."""
        # Highlight bar (spans full card width, inset)
        hl_x = card_x + 4
        hl_w = card_w - 8
        hl = QGraphicsRectItem()
        hl.setRect(hl_x, y + 1, hl_w, self.ROW_HEIGHT - 2)
        hl.setBrush(QBrush(self.HIGHLIGHT_BG))
        hl.setPen(QPen(Qt.PenStyle.NoPen))
        hl.setZValue(-5)
        hl.setVisible(highlighted)
        self.scene.addItem(hl)
        if sid is not None:
            self._hl_rects[sid] = hl

        # Rounded dot indicator (circle)
        dot_r = self.DOT_SIZE / 2
        dot_x = x + 2
        dot_y = y + (self.ROW_HEIGHT - self.DOT_SIZE) / 2
        dot_path = QPainterPath()
        dot_path.addEllipse(dot_x + dot_r, dot_y + dot_r, dot_r, dot_r)
        dot = QGraphicsPathItem(dot_path)
        dot.setBrush(QBrush(self.HIGHLIGHT_BORDER if highlighted else self.BOOKMARK_DOT))
        dot.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(dot)

        # Text label
        text_x = x + self.DOT_SIZE + 6
        text_avail = avail_w - self.DOT_SIZE - 8
        truncated = self._truncate(text, fm, text_avail)

        lbl = QGraphicsSimpleTextItem(truncated)
        lbl.setPos(text_x, y + 4)
        lbl.setFont(font)
        lbl.setBrush(self.HIGHLIGHT_BORDER if highlighted else self.BOOKMARK_TEXT)
        self.scene.addItem(lbl)

    def _truncate(self, text: str, fm: QFontMetrics, max_w: float) -> str:
        """Truncate text with ellipsis to fit within max_w pixels."""
        if fm.horizontalAdvance(text) <= max_w:
            return text
        while len(text) > 1 and fm.horizontalAdvance(text + "...") > max_w:
            text = text[:-1]
        return text + "..."


class ScriptDialog(QDialog):
    """Dialog for creating or editing a Chrome JS bookmarklet."""

    def __init__(self, parent=None, script_data=None, existing_folders=None):
        super().__init__(parent)
        self.script_data = script_data
        self.is_edit_mode = script_data is not None
        self.existing_folders = existing_folders or []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("编辑 Chrome JS脚本" if self.is_edit_mode else "新增 Chrome JS脚本")
        self.setMinimumSize(680, 520)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name
        layout.addWidget(QLabel("脚本名称"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：导出表格CSV、显示密码")
        self.name_input.setMinimumHeight(32)
        layout.addWidget(self.name_input)

        # Folder + Position row
        row = QHBoxLayout()
        row.setSpacing(12)

        folder_wrap = QVBoxLayout()
        folder_wrap.addWidget(QLabel("子文件夹（可选）"))
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(True)
        self.folder_combo.setMinimumHeight(32)
        self.folder_combo.setMinimumWidth(200)
        self.folder_combo.setPlaceholderText("留空 = 直接放在 JS Scripts")
        self.folder_combo.addItem("")  # empty = root
        for f in sorted(set(self.existing_folders)):
            if f:
                self.folder_combo.addItem(f)
        self.folder_combo.setCurrentIndex(0)
        folder_wrap.addWidget(self.folder_combo)
        row.addLayout(folder_wrap, 3)

        pos_wrap = QVBoxLayout()
        pos_wrap.addWidget(QLabel("排序"))
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("越小越靠前")
        self.position_input.setFixedWidth(100)
        self.position_input.setMinimumHeight(32)
        pos_wrap.addWidget(self.position_input)
        row.addLayout(pos_wrap, 1)

        layout.addLayout(row)

        # Description (multi-line)
        layout.addWidget(QLabel("功能描述"))
        self.desc_input = QTextEdit()
        self.desc_input.setFont(QFont("Microsoft YaHei", 9))
        self.desc_input.setPlaceholderText("脚本功能描述（可选）")
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setAcceptRichText(False)
        layout.addWidget(self.desc_input)

        # URL (multi-line, below folder)
        layout.addWidget(QLabel("脚本 URL (bookmarklet 或远程地址)"))
        self.url_input = QTextEdit()
        self.url_input.setFont(QFont("Consolas", 10))
        self.url_input.setPlaceholderText("javascript:(function(){ /* your code */ })()")
        self.url_input.setMinimumHeight(120)
        self.url_input.setAcceptRichText(False)
        layout.addWidget(self.url_input, 1)

        # Tip
        tip = QLabel("Tip: bookmarklet 格式 javascript:(function(){...})()；支持 http/https/file 协议")
        tip.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(tip)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(100)
        save_btn.setDefault(True)
        save_btn.setStyleSheet("QPushButton { background-color: #0078D4; color: white; border: none; padding: 8px 16px; } QPushButton:hover { background-color: #006cbd; }")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_data(self):
        if self.is_edit_mode and self.script_data:
            self.name_input.setText(self.script_data.get("name", ""))
            self.desc_input.setPlainText(self.script_data.get("description", ""))
            self.url_input.setPlainText(self.script_data.get("url", ""))
            folder = self.script_data.get("parent_folder", "")
            idx = self.folder_combo.findText(folder)
            if idx >= 0:
                self.folder_combo.setCurrentIndex(idx)
            else:
                self.folder_combo.setEditText(folder)
            self.position_input.setText(str(self.script_data.get("position", 0)))

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return

        url = self.url_input.toPlainText().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入脚本 URL")
            return

        self.accept()

    def get_script_data(self):
        try:
            position = int(self.position_input.text().strip() or 0)
        except ValueError:
            position = 0

        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "url": self.url_input.toPlainText().strip(),
            "parent_folder": self.folder_combo.currentText().strip(),
            "position": position,
        }


class JsModule(QWidget):
    """Chrome JS 脚本管理模块（bookmarklet 部署）."""

    script_added = pyqtSignal()
    script_deleted = pyqtSignal()
    script_updated = pyqtSignal()

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path

        from services.js_service import JsService
        self.js_service = JsService(db_path)

        self._setup_ui()
        self._refresh_list()
        self._refresh_preview()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ---- Title ----
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        title_label = QLabel("Chrome JS 脚本管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 5px 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
        title_label.setFixedHeight(35)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout, 0)

        # ---- Toolbar ----
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        toolbar_layout.setContentsMargins(0, 0, 0, 5)

        self.add_btn = QPushButton("+ 新增")
        self.add_btn.setFixedHeight(35)
        self.add_btn.setStyleSheet(self._btn_style("#107c10"))
        self.add_btn.clicked.connect(self._on_add_script)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("修改")
        self.edit_btn.setFixedHeight(35)
        self.edit_btn.setStyleSheet(self._btn_style("#0078D4"))
        self.edit_btn.clicked.connect(self._on_edit_script)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFixedHeight(35)
        self.delete_btn.setStyleSheet(self._btn_style("#d83b01"))
        self.delete_btn.clicked.connect(self._on_delete_script)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addSpacing(20)

        self.open_btn = QPushButton("在 Chrome 中打开")
        self.open_btn.setFixedHeight(35)
        self.open_btn.setStyleSheet(self._btn_style("#4285F4"))
        self.open_btn.clicked.connect(self._on_open_in_chrome)
        toolbar_layout.addWidget(self.open_btn)

        self.deploy_btn = QPushButton("部署到 Chrome")
        self.deploy_btn.setFixedHeight(35)
        self.deploy_btn.setStyleSheet(self._btn_style("#009900"))
        self.deploy_btn.clicked.connect(self._on_deploy_bookmarks)
        toolbar_layout.addWidget(self.deploy_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout, 0)

        # ---- Path row ----
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 2)
        self.path_label = QLabel("书签路径：未设置")
        self.path_label.setStyleSheet("color: #aaa; font-size: 11px;")
        path_layout.addWidget(self.path_label)
        path_layout.addStretch()
        layout.addLayout(path_layout, 0)

        # ---- Main content: horizontal split (preview | right panel) ----
        hsplit = QSplitter(Qt.Orientation.Horizontal)
        hsplit.setChildrenCollapsible(False)

        # === Left: Bookmark Preview ===
        preview_panel = QFrame()
        pl = QVBoxLayout()
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(3)

        pl_hdr = QLabel("书签栏预览")
        pl_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        pl_hdr.setFixedHeight(24)
        pl.addWidget(pl_hdr)

        self.bookmark_preview = BookmarkPreviewView()
        pl.addWidget(self.bookmark_preview)

        preview_panel.setLayout(pl)

        # === Right: vertical split (list top / details bottom) ===
        vsplit = QSplitter(Qt.Orientation.Vertical)

        # -- Script list panel --
        list_panel = QFrame()
        ll = QVBoxLayout()
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(0)

        list_hdr = QLabel("脚本列表")
        list_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        list_hdr.setFixedHeight(24)
        ll.addWidget(list_hdr)

        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.itemSelectionChanged.connect(self._on_selection_changed)
        ll.addWidget(self.script_list)

        list_panel.setLayout(ll)

        # -- Details panel --
        detail_panel = QFrame()
        detail_panel.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        dl = QVBoxLayout()
        dl.setContentsMargins(6, 4, 6, 4)
        dl.setSpacing(3)

        dl_hdr = QLabel("脚本信息")
        dl_hdr.setStyleSheet("font-weight: bold; padding: 3px; background: #e8e8e8;")
        dl_hdr.setFixedHeight(24)
        dl.addWidget(dl_hdr)

        self.detail_form = QFormLayout()
        self.detail_form.setSpacing(10)

        self.detail_name = QLabel("-")
        self.detail_desc = QLabel("-")
        self.detail_desc.setWordWrap(True)
        self.detail_url = QLabel("-")
        self.detail_url.setWordWrap(True)
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_folder = QLabel("-")
        self.detail_pos = QLabel("-")

        self.detail_form.addRow("脚本名称:", self.detail_name)
        self.detail_form.addRow("功能描述:", self.detail_desc)
        self.detail_form.addRow("URL:", self.detail_url)
        self.detail_form.addRow("书签文件夹:", self.detail_folder)
        self.detail_form.addRow("排序位置:", self.detail_pos)

        dl.addLayout(self.detail_form)
        dl.addStretch()
        detail_panel.setLayout(dl)

        vsplit.addWidget(list_panel)
        vsplit.addWidget(detail_panel)
        vsplit.setStretchFactor(0, 3)
        vsplit.setStretchFactor(1, 1)

        hsplit.addWidget(preview_panel)
        hsplit.addWidget(vsplit)
        hsplit.setStretchFactor(0, 1)
        hsplit.setStretchFactor(1, 3)
        hsplit.setSizes([220, 500])

        layout.addWidget(hsplit, 1)
        self.setLayout(layout)

    def _btn_style(self, color):
        return f"""
            QPushButton {{ background-color: {color}; color: white; border: none;
                padding: 4px 14px; border-radius: 4px; font-size: 12px; }}
            QPushButton:hover {{ opacity: 0.9; }}
        """

    # ---- List & selection ----

    def _refresh_list(self):
        self.script_list.clear()
        scripts = self.js_service.get_all_scripts()
        last_folder = None
        for s in scripts:
            desc = s.get("description", "")
            label = s["name"]
            if desc:
                label += f"  —  {desc}"
            folder = s.get("parent_folder", "")
            if folder != last_folder:
                folder_name = folder or "JS Scripts"
                header = QListWidgetItem(f"> {folder_name}")
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setData(Qt.ItemDataRole.UserRole, None)
                font = header.font()
                font.setBold(True)
                header.setFont(font)
                header.setForeground(Qt.GlobalColor.gray)
                self.script_list.addItem(header)
                last_folder = folder
            item = QListWidgetItem(f"    {label}")
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self.script_list.addItem(item)

    def _on_selection_changed(self):
        sel = self.script_list.selectedItems()
        if not sel:
            self._clear_details()
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if sid is None:
            return
        if sid:
            script = self.js_service.get_script(sid)
            if script:
                self._show_details(script)

    def _clear_details(self):
        for w in [self.detail_name, self.detail_desc, self.detail_url, self.detail_folder, self.detail_pos]:
            w.setText("-")

    def _show_details(self, s):
        self.detail_name.setText(s.get("name", "-"))
        self.detail_desc.setText(s.get("description", "") or "-")
        url = s.get("url", "-")
        if len(url) > 200:
            url = url[:197] + "..."
        self.detail_url.setText(url)
        self.detail_folder.setText(s.get("parent_folder", "") or "JS Scripts")
        self.detail_pos.setText(str(s.get("position", 0)))

    # ---- Preview ----

    def _refresh_preview(self, highlight_id=None):
        """Full data refresh — called on add/edit/delete. Rebuilds scene."""
        scripts = self.js_service.get_all_scripts()
        self.bookmark_preview.show_preview(scripts, highlight_id=highlight_id)

    def _highlight_preview(self, highlight_id=None):
        """Deferred full refresh — QTimer breaks the synchronous call chain
        so the QSplitter finishes its layout before the scene rebuilds."""
        scripts = self.js_service.get_all_scripts()
        QTimer.singleShot(0, lambda: self.bookmark_preview.show_preview(scripts, highlight_id=highlight_id))

    # ---- CRUD ----

    def _on_add_script(self):
        try:
            folders = self._collect_folders()
            dlg = ScriptDialog(self, existing_folders=folders)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                data = dlg.get_script_data()
                try:
                    self.js_service.add_script(name=data["name"], url=data["url"],
                                               parent_folder=data["parent_folder"],
                                               position=data["position"],
                                               description=data["description"])
                except ValueError as e:
                    QMessageBox.warning(self, "保存失败", str(e))
                    return
                self._refresh_list()
                self._refresh_preview()
                self.script_added.emit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存脚本时发生错误:\n{type(e).__name__}: {e}")

    def _on_edit_script(self):
        sel = self.script_list.selectedItems()
        if not sel:
            QMessageBox.warning(self, "警告", "请选择要修改的脚本")
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            QMessageBox.warning(self, "警告", "请选择脚本条目而非文件夹标题")
            return
        script = self.js_service.get_script(sid)
        if not script:
            return

        folders = self._collect_folders()
        dlg = ScriptDialog(self, script_data=script, existing_folders=folders)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_script_data()
            self.js_service.update_script(sid, name=data["name"], url=data["url"],
                                          description=data["description"],
                                          parent_folder=data["parent_folder"],
                                          position=data["position"])
            self._refresh_list()
            self._refresh_preview(highlight_id=sid)
            self.script_updated.emit()

    def _on_delete_script(self):
        sel = self.script_list.selectedItems()
        if not sel:
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            return
        reply = QMessageBox.question(self, "确认删除", "确定要删除选中的脚本吗？")
        if reply == QMessageBox.StandardButton.Yes:
            if self.js_service.delete_script(sid):
                self._refresh_list()
                self._clear_details()
                self._refresh_preview()
                self.script_deleted.emit()

    def _collect_folders(self):
        folders = set()
        for s in self.js_service.get_all_scripts():
            f = s.get("parent_folder", "")
            if f:
                folders.add(f)
        return list(folders)

    # ---- Deploy ----

    def _on_deploy_bookmarks(self):
        if not self.js_service.chrome_path:
            QMessageBox.warning(self, "警告", "请先在全局设置中配置 Chrome 书签路径")
            return

        result = self.js_service.deploy_bookmarks()

        if result["success"]:
            self._refresh_preview()
            QMessageBox.information(self, "部署成功", result["message"])
        else:
            QMessageBox.warning(self, "部署失败", result["message"])

    # ---- Open in Chrome ----

    def _on_open_in_chrome(self):
        sel = self.script_list.selectedItems()
        if not sel:
            QMessageBox.warning(self, "警告", "请选择要打开的脚本")
            return
        sid = sel[0].data(Qt.ItemDataRole.UserRole)
        if not sid:
            QMessageBox.warning(self, "警告", "请选择脚本条目而非文件夹标题")
            return
        ok = self.js_service.open_in_chrome(sid)
        if not ok:
            QMessageBox.warning(self, "警告", "无法在 Chrome 中打开脚本")

    # ---- Global path ----

    def set_chrome_path(self, path: str):
        self.js_service.set_chrome_path(path)
        if path:
            self.path_label.setText(f"书签路径：{path}")
            self.path_label.setStyleSheet("color: #107c10; font-size: 11px;")
        else:
            self.path_label.setText("书签路径：未设置")
            self.path_label.setStyleSheet("color: #aaa; font-size: 11px;")
