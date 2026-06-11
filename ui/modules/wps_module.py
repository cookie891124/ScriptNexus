"""WpsModule - WPS script management with Visual Ribbon Builder."""

import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QTextEdit, QLabel, QDialog, QLineEdit,
    QMessageBox, QSplitter, QFrame, QComboBox, QFormLayout,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QMenu,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem,
    QInputDialog, QButtonGroup, QToolButton, QTextBrowser, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSize, QRegularExpression
from PyQt6.QtGui import (
    QFont, QColor, QBrush, QPen, QPainter, QAction, QIcon, QFontMetrics,
    QSyntaxHighlighter, QTextCharFormat, QKeySequence
)
from PyQt6.QtWidgets import QGraphicsItem
from services.wps_service import WpsService
from ui.theme import set_button_variant

# ===== Ribbon Tree Item =====

class _RibbonTreeItem(QTreeWidgetItem):
    """QTreeWidgetItem with complex data in a Python attribute."""

    def __init__(self, text, data=None):
        super().__init__(text)
        self.item_data = data or {}


# ===== JavaScript Syntax Highlighter =====

class JsaSyntaxHighlighter(QSyntaxHighlighter):
    """JavaScript syntax highlighter for code editor."""

    def __init__(self, document):
        super().__init__(document)

        # 定义格式
        self.formats = {}
        self.highlightRules = []

        # 关键字 - 蓝色粗体
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = ["function", "var", "let", "const", "if", "else", "for", "while",
                    "do", "switch", "case", "break", "continue", "return", "try",
                    "catch", "finally", "throw", "new", "this", "class", "extends",
                    "import", "export", "default", "async", "await", "typeof", "instanceof",
                    "true", "false", "null", "undefined", "void", "in", "of"]
        for word in keywords:
            pattern = QRegularExpression(r"\b" + word + r"\b")
            self.highlightRules.append((pattern, keyword_format))

        # 内置函数 - 深蓝色
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#0078D4"))
        builtins = ["MsgBox", "Alert", "Console", "log", "parseInt", "parseFloat",
                    "toString", "valueOf", "length", "push", "pop", "shift", "slice",
                    "split", "join", "indexOf", "replace", "trim", "toLowerCase",
                    "toUpperCase", "Object", "Array", "String", "Number", "Boolean",
                    "Math", "Date", "JSON", "RegExp", "Error", "setTimeout", "setInterval"]
        for word in builtins:
            pattern = QRegularExpression(r"\b" + word + r"\b")
            self.highlightRules.append((pattern, builtin_format))

        # 字符串 - 绿色
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        self.highlightRules.append((QRegularExpression(r"'[^']*'"), string_format))
        self.highlightRules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # 数字 - 橙色
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF6600"))
        self.highlightRules.append((QRegularExpression(r"\b[0-9]+\.?[0-9]*\b"), number_format))

        # 注释 - 灰色斜体
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)
        self.highlightRules.append((QRegularExpression(r"//.*"), comment_format))
        self.highlightRules.append((QRegularExpression(r"/\*.*\*/"), comment_format))

        # 函数名 - 深绿色
        func_name_format = QTextCharFormat()
        func_name_format.setForeground(QColor("#006600"))
        self.highlightRules.append((QRegularExpression(r"\bfunction\s+(\w+)"), func_name_format))

        # 括号错误格式 - 红色
        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(QColor("#FF0000"))

        # 错误格式 - 红色背景
        self.error_format = QTextCharFormat()
        self.error_format.setBackground(QColor("#FFEEEE"))
        self.error_format.setForeground(QColor("#CC0000"))

    def highlightBlock(self, text):
        """Apply highlighting to a block of text."""
        # 应用规则
        for pattern, format in self.highlightRules:
            matchIterator = pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        # 注意：括号匹配检查移到全局检查中，不在行级处理


# ===== Ribbon Preview =====

class RibbonPreviewView(QGraphicsView):
    """Visual ribbon preview showing the selected tab's structure in WPS style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumHeight(90)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scene.setSceneRect(0, 0, self.width(), 90)

    def clear_preview(self):
        """Clear all items from preview."""
        self.scene.clear()

    def show_tab_preview(self, tab_name, groups_with_buttons):
        """Show preview of a tab with its groups and buttons in WPS style."""
        self.scene.clear()

        w = self.width()
        h = 90

        # Draw main ribbon background (white)
        ribbon_bg = QGraphicsRectItem()
        ribbon_bg.setRect(0, 0, w, h)
        ribbon_bg.setBrush(QBrush(QColor("#FFFFFF")))
        ribbon_bg.setPen(QPen(QColor("#D4D4D4"), 1))
        ribbon_bg.setZValue(-2)
        self.scene.addItem(ribbon_bg)

        # Draw tab bar area (top strip) - 紧贴标签
        tab_bar = QGraphicsRectItem()
        tab_bar.setRect(0, 0, w, 28)
        tab_bar.setBrush(QBrush(QColor("#F3F3F3")))
        tab_bar.setPen(QPen(Qt.PenStyle.NoPen))
        tab_bar.setZValue(-1)
        self.scene.addItem(tab_bar)

        if not groups_with_buttons:
            # 仅显示当前Tab标签
            tab_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            fm = QFontMetrics(tab_font)
            tab_w = max(60, min(fm.horizontalAdvance(tab_name) + 16, 120))
            tab_h = 24
            tab_x = 10
            tab_y = 2

            selected_tab_bg = QGraphicsRectItem()
            selected_tab_bg.setRect(tab_x, tab_y, tab_w, tab_h)
            selected_tab_bg.setBrush(QBrush(QColor("#FFFFFF")))
            selected_tab_bg.setPen(QPen(QColor("#D4D4D4"), 1))
            self.scene.addItem(selected_tab_bg)

            tab_text = QGraphicsSimpleTextItem(tab_name, selected_tab_bg)
            text_w = fm.horizontalAdvance(tab_name)
            tab_text.setPos(tab_x + (tab_w - text_w) / 2, tab_y + 5)
            tab_text.setFont(tab_font)
            tab_text.setBrush(QColor("#1E1E1E"))
            return

        # Draw groups and buttons - 紧凑布局，按钮宽度自适应
        x_offset = 8
        y_offset = 30

        btn_font = QFont("Segoe UI", 8)
        btn_fm = QFontMetrics(btn_font)
        group_font = QFont("Segoe UI", 8, QFont.Weight.Bold)

        for group_name, button_labels in groups_with_buttons:
            # 计算按钮宽度 - 根据文本长度自适应
            btn_widths = []
            for label in button_labels:
                text_w = btn_fm.horizontalAdvance(label)
                btn_w = max(45, min(text_w + 18, 100))  # 最小45，最大100
                btn_widths.append(btn_w)

            # 每行最多显示按钮数量
            max_per_row = 3
            rows = (len(button_labels) + 2) // 3

            # 计算分组宽度
            max_row_width = 0
            for i in range(rows):
                row_start = i * max_per_row
                row_end = min(row_start + max_per_row, len(button_labels))
                row_width = sum(btn_widths[row_start:row_end]) + (row_end - row_start - 1) * 4 + 10
                max_row_width = max(max_row_width, row_width)

            group_label_w = btn_fm.horizontalAdvance(group_name) + 12
            group_width = max(group_label_w + 6, max_row_width)
            group_height = 18 + rows * 22  # 紧凑高度

            # Group background
            group_rect = QGraphicsRectItem()
            group_rect.setRect(x_offset, y_offset, group_width, group_height)
            group_rect.setBrush(QBrush(QColor("#F8F8F8")))
            group_rect.setPen(QPen(QColor("#E0E0E0"), 1))
            self.scene.addItem(group_rect)

            # Group label
            group_label = QGraphicsSimpleTextItem(group_name, group_rect)
            group_label.setPos(x_offset + 4, y_offset + 2)
            group_label.setFont(group_font)
            group_label.setBrush(QColor("#666666"))

            # Buttons - 自适应宽度
            btn_y = y_offset + 16
            col = 0
            btn_x = x_offset + 4

            for idx, btn_label in enumerate(button_labels):
                btn_w = btn_widths[idx]

                if col >= max_per_row:
                    col = 0
                    btn_x = x_offset + 4
                    btn_y += 22

                # Button background
                btn_rect = QGraphicsRectItem()
                btn_rect.setRect(btn_x, btn_y, btn_w, 18)
                btn_rect.setBrush(QBrush(QColor("#FFFFFF")))
                btn_rect.setPen(QPen(QColor("#C8C8C8"), 1))
                self.scene.addItem(btn_rect)

                # Button icon placeholder
                icon_rect = QGraphicsRectItem()
                icon_rect.setRect(btn_x + 2, btn_y + 3, 10, 10)
                icon_rect.setBrush(QBrush(QColor("#4A90D9")))
                icon_rect.setPen(QPen(Qt.PenStyle.NoPen))
                self.scene.addItem(icon_rect)

                # Button text - 显示完整文本（已自适应宽度）
                btn_text = QGraphicsSimpleTextItem(btn_label, btn_rect)
                btn_text.setPos(btn_x + 14, btn_y + 4)
                btn_text.setFont(btn_font)
                btn_text.setBrush(QColor("#333333"))

                btn_x += btn_w + 4
                col += 1

            x_offset += group_width + 6


# ===== Ribbon Tree Panel =====

class RibbonTreePanel(QWidget):
    """Left panel showing ribbon structure as tree.

    使用独立的功能区结构表 (ribbon_tabs, ribbon_groups, ribbon_buttons),
    与脚本表 (wps_scripts) 分离。只有通过"绑定脚本"操作才将按钮和脚本关联。
    """

    def __init__(self, parent=None, main_module=None):
        super().__init__(parent)
        self.wps_service = None
        self.current_app = "word"
        self.current_tab_id = None  # 当前选中的 Tab ID
        self.current_tab_name = None  # 当前选中的 Tab 名称（用于显示）
        self.main_module = main_module
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        # Header - tabs row + group add button
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #E0E0E0;")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(5, 2, 5, 2)
        header_layout.setSpacing(2)

        # Tabs row
        self.tab_container = QWidget()
        self.tab_container.setStyleSheet("background-color: transparent;")
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(2)
        self.tab_container.setLayout(self.tab_layout)
        header_layout.addWidget(self.tab_container)

        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        # Reorder buttons — compact bar between header and tree
        reorder_bar = QWidget()
        reorder_bar.setFixedHeight(26)
        reorder_bar.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #ddd;")
        reorder_layout = QHBoxLayout()
        reorder_layout.setContentsMargins(8, 0, 8, 0)
        reorder_layout.setSpacing(4)

        lbl = QLabel("排序:")
        lbl.setStyleSheet("font-size: 10px; color: #888; border: none;")
        reorder_layout.addWidget(lbl)

        self.btn_up = QPushButton("↑")
        self.btn_up.setFixedSize(26, 20)
        self.btn_up.setToolTip("上移")
        self.btn_up.setStyleSheet("QPushButton { font-size: 12px; background: #e8e8e8; border: 1px solid #ccc; border-radius: 3px; } QPushButton:hover { background: #d0d0d0; }")
        self.btn_up.clicked.connect(self._move_up)
        reorder_layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("↓")
        self.btn_down.setFixedSize(26, 20)
        self.btn_down.setToolTip("下移")
        self.btn_down.setStyleSheet("QPushButton { font-size: 12px; background: #e8e8e8; border: 1px solid #ccc; border-radius: 3px; } QPushButton:hover { background: #d0d0d0; }")
        self.btn_down.clicked.connect(self._move_down)
        reorder_layout.addWidget(self.btn_down)

        reorder_layout.addStretch()
        reorder_bar.setLayout(reorder_layout)
        layout.addWidget(reorder_bar)

        # Tree widget for groups and buttons
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: #FAFAFA;
            }
            QTreeWidget::item {
                padding: 4px;
            }
        """)
        layout.addWidget(self.tree, 1)

        self.setLayout(layout)

    def set_wps_service(self, service):
        self.wps_service = service

    def set_app(self, app):
        self.current_app = app

    def refresh_tabs(self):
        """Refresh tab buttons from ribbon_tabs table."""
        # Clear existing tabs
        while self.tab_layout.count():
            item = self.tab_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.wps_service:
            return

        # Get tabs from ribbon_tabs table
        tabs = self.wps_service.get_all_tabs(self.current_app)

        # Check if current_tab_id belongs to current_app
        current_tab_valid = False
        if tabs:
            for tab in tabs:
                if tab["id"] == self.current_tab_id:
                    current_tab_valid = True
                    break

        # If current_tab_id is not valid for this app, reset to first tab
        if not current_tab_valid:
            if tabs:
                self.current_tab_id = tabs[0]["id"]
                self.current_tab_name = tabs[0]["name"]
            else:
                self.current_tab_id = None
                self.current_tab_name = None

        # Create tab buttons
        if tabs:
            for tab in tabs:
                tab_btn = QToolButton()
                tab_btn.setText(tab["name"])
                tab_btn.setFixedHeight(26)
                tab_btn.setCheckable(True)
                is_current = tab["id"] == self.current_tab_id
                tab_btn.setChecked(is_current)
                if is_current:
                    self.current_tab_name = tab["name"]
                tab_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #717171;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 0 12px;
                        font-size: 12px;
                    }
                    QToolButton:hover {
                        background-color: #555;
                    }
                    QToolButton:checked {
                        background-color: #2D5E8C;
                    }
                """)
                # Store tab info
                tab_btn.tab_id = tab["id"]
                tab_btn.tab_name = tab["name"]
                # Left click to select tab
                tab_btn.clicked.connect(lambda checked, t=tab: self._on_tab_clicked(t))
                # Right click for context menu
                tab_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                tab_btn.customContextMenuRequested.connect(lambda pos, btn=tab_btn: self._show_tab_context_menu(btn, pos))
                self.tab_layout.addWidget(tab_btn)
        else:
            # No tabs - show hint
            empty_label = QLabel("暂无 Tab，右键树区域新增")
            empty_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 12px;
                    padding: 5px;
                    background: transparent;
                    border: none;
                }
            """)
            self.tab_layout.addWidget(empty_label)
            self.current_tab_id = None
            self.current_tab_name = None

        self.tab_layout.addStretch()

    def _show_tab_context_menu(self, btn, pos):
        """Show context menu for tab button."""
        tab_id = btn.tab_id
        tab_name = btn.tab_name
        menu = QMenu()

        # 本级操作
        action_add_tab = QAction("新增 Tab", self)
        action_add_tab.triggered.connect(self._on_add_tab)
        menu.addAction(action_add_tab)

        action_delete = QAction("删除 Tab", self)
        action_delete.triggered.connect(lambda: self._on_delete_tab(tab_id, tab_name))
        menu.addAction(action_delete)

        action_rename = QAction("重命名 Tab", self)
        action_rename.triggered.connect(lambda: self._on_rename_tab(tab_id, tab_name))
        menu.addAction(action_rename)

        # 分割线 - 区分本级与下级
        menu.addSeparator()

        # 下级操作
        action_add_group = QAction("新增分组", self)
        action_add_group.triggered.connect(lambda: self._on_add_group(tab_id))
        menu.addAction(action_add_group)

        menu.exec(btn.mapToGlobal(pos))

    def _on_tab_clicked(self, tab):
        """Handle tab button click."""
        self.current_tab_id = tab["id"]
        self.current_tab_name = tab["name"]
        self.refresh_tabs()
        self.refresh_tree()
        self.main_module.show_tab_preview(tab["name"])

    def refresh_tree(self):
        """Refresh tree from structure tables."""
        self.tree.clear()
        if not self.wps_service or not self.current_tab_id:
            return

        # Get groups for this tab
        groups = self.wps_service.get_all_groups(self.current_tab_id)

        # No groups - show hint (与Tab设计一致)
        if not groups:
            hint_item = _RibbonTreeItem(["暂无分组，右键Tab新增分组"], {"type": "hint"})
            hint_item.setFlags(hint_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(hint_item)
            return

        for group in groups:
            group_item = _RibbonTreeItem(["📁 " + group["name"]], {
                "type": "group",
                "id": group["id"],
                "tab_id": self.current_tab_id,
                "name": group["name"]
            })
            group_item.setExpanded(True)

            # Get buttons for this group
            buttons = self.wps_service.get_all_buttons(group["id"])

            for button in buttons:
                # Check if button has bound script
                script_name = button.get("script_name") or ""
                if button.get("script_id") and script_name:
                    display_text = f"🔘 {button['label']} [绑定: {script_name}]"
                else:
                    display_text = f"🔘 {button['label']} [未绑定]"

                btn_item = _RibbonTreeItem([display_text], {
                    "type": "button",
                    "id": button["id"],
                    "group_id": group["id"],
                    "tab_id": self.current_tab_id,
                    "label": button["label"],
                    "script_id": button.get("script_id")
                })
                group_item.addChild(btn_item)

            self.tree.addTopLevelItem(group_item)

    def refresh_all(self):
        """Refresh both tabs and tree."""
        self.refresh_tabs()
        self.refresh_tree()
        if self.current_tab_name:
            self.main_module.show_tab_preview(self.current_tab_name)
        else:
            self.main_module.refresh_preview()

    def get_selected_script_id(self):
        """Get the script ID of selected button (if bound)."""
        item = self.tree.currentItem()
        if not item:
            return None
        data = item.item_data if hasattr(item, "item_data") else {}
        if data and data.get("type") == "button":
            return data.get("script_id")
        return None

    def _persist_tree_order(self):
        """Persist current tree order to DB after drag-and-drop."""
        if not self.wps_service or not self.current_tab_id:
            return
        group_order = []
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            group_data = group_item.item_data if hasattr(group_item, "item_data") else {}
            if group_data and group_data.get("type") == "group":
                gid = group_data["id"]
                group_order.append(gid)
                button_order = []
                for j in range(group_item.childCount()):
                    btn_item = group_item.child(j)
                    btn_data = btn_item.item_data if hasattr(btn_item, "item_data") else {}
                    if btn_data and btn_data.get("type") == "button":
                        bid = btn_data["id"]
                        button_order.append(bid)
                        old_group_id = btn_data.get("group_id")
                        if old_group_id and old_group_id != gid:
                            self.wps_service.move_button_to_group(bid, gid)
                            btn_data["group_id"] = gid
                if button_order:
                    self.wps_service.update_button_positions(button_order)
        if group_order:
            self.wps_service.update_group_positions(self.current_tab_id, group_order)

    # ── Move up / down ──

    def _move_up(self):
        item = self.tree.currentItem()
        if not item:
            return
        data = item.item_data if hasattr(item, "item_data") else {}
        item_type = data.get("type")

        if item_type == "group":
            self._move_group(item, -1)
        elif item_type == "button":
            self._move_button(item, -1)

        self._after_move()

    def _move_down(self):
        item = self.tree.currentItem()
        if not item:
            return
        data = item.item_data if hasattr(item, "item_data") else {}
        item_type = data.get("type")

        if item_type == "group":
            self._move_group(item, 1)
        elif item_type == "button":
            self._move_button(item, 1)

        self._after_move()

    def _move_group(self, item, direction):
        """Move group up (-1) or down (+1) among top-level items."""
        parent = item.parent()
        if parent:
            idx = parent.indexOfChild(item)
            parent.takeChild(idx)
            new_idx = idx + direction
            if new_idx < 0:
                new_idx = parent.childCount()
            elif new_idx > parent.childCount():
                new_idx = 0
            parent.insertChild(new_idx, item)
        else:
            idx = self.tree.indexOfTopLevelItem(item)
            if idx < 0:
                return
            self.tree.takeTopLevelItem(idx)
            new_idx = idx + direction
            count = self.tree.topLevelItemCount()
            if new_idx < 0:
                new_idx = count
            elif new_idx > count:
                new_idx = 0
            self.tree.insertTopLevelItem(new_idx, item)
        self.tree.setCurrentItem(item)

    def _move_button(self, item, direction):
        """Move button up (-1) or down (+1). Cross group boundaries."""
        parent = item.parent()
        if not parent:
            return
        idx = parent.indexOfChild(item)
        new_idx = idx + direction
        if 0 <= new_idx < parent.childCount():
            # Move within same group
            parent.takeChild(idx)
            parent.insertChild(new_idx, item)
        else:
            # Cross group boundary
            grandparent = parent.parent()
            if grandparent:
                gi = grandparent.indexOfChild(parent)
            else:
                gi = self.tree.indexOfTopLevelItem(parent)
            target_gi = gi + direction
            # Find target group
            if grandparent:
                if 0 <= target_gi < grandparent.childCount():
                    target_group = grandparent.child(target_gi)
                else:
                    return
            else:
                if 0 <= target_gi < self.tree.topLevelItemCount():
                    target_group = self.tree.topLevelItem(target_gi)
                else:
                    return
            tdata = target_group.item_data if hasattr(target_group, "item_data") else {}
            if tdata.get("type") != "group":
                return
            parent.takeChild(idx)
            if direction == -1:
                target_group.addChild(item)
            else:
                target_group.insertChild(0, item)
        self.tree.setCurrentItem(item)

    def _after_move(self):
        self._persist_tree_order()
        if self.main_module:
            self.main_module.refresh_preview()

    def _on_item_clicked(self, item, column):
        """Handle tree item click - load bound script in editor."""
        data = item.item_data if hasattr(item, "item_data") else {}
        if not data:
            return

        if data.get("type") == "button":
            script_id = data.get("script_id")
            if script_id:
                script = self.wps_service.get_script(script_id)
                if script:
                    self.main_module.load_script_in_editor(script)

    def _on_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            # 空白区域右键 - 提供新增Tab/分组入口
            menu = QMenu()
            action_add_tab = QAction("新增 Tab", self)
            action_add_tab.triggered.connect(self._on_add_tab)
            menu.addAction(action_add_tab)
            if self.current_tab_id:
                action_add_group = QAction("新增分组", self)
                action_add_group.triggered.connect(lambda: self._on_add_group(self.current_tab_id))
                menu.addAction(action_add_group)
            menu.exec(self.tree.viewport().mapToGlobal(position))
            return

        data = item.item_data if hasattr(item, "item_data") else {}
        if not data or data.get("type") == "hint":
            # 点击提示项或无数据项，也显示空白区域菜单
            menu = QMenu()
            action_add_tab = QAction("新增 Tab", self)
            action_add_tab.triggered.connect(self._on_add_tab)
            menu.addAction(action_add_tab)
            if self.current_tab_id:
                action_add_group = QAction("新增分组", self)
                action_add_group.triggered.connect(lambda: self._on_add_group(self.current_tab_id))
                menu.addAction(action_add_group)
            menu.exec(self.tree.viewport().mapToGlobal(position))
            return

        menu = QMenu()

        if data.get("type") == "group":
            # Group level menu - 本级操作
            action_add_group = QAction("新增分组", self)
            action_add_group.triggered.connect(lambda: self._on_add_group(data.get("tab_id")))
            menu.addAction(action_add_group)

            action_delete = QAction("删除分组", self)
            action_delete.triggered.connect(lambda: self._on_delete_group(data.get("id"), data.get("name")))
            menu.addAction(action_delete)

            action_rename = QAction("重命名分组", self)
            action_rename.triggered.connect(lambda: self._on_rename_group(data.get("id"), data.get("name")))
            menu.addAction(action_rename)

            # 分割线 - 区分本级与下级
            menu.addSeparator()

            # 下级操作
            action_add_btn = QAction("新增按钮", self)
            action_add_btn.triggered.connect(lambda: self._on_add_button(data.get("id")))
            menu.addAction(action_add_btn)

        elif data.get("type") == "button":
            # Button level menu - 本级操作
            action_add = QAction("新增按钮", self)
            action_add.triggered.connect(lambda: self._on_add_button(data.get("group_id")))
            menu.addAction(action_add)

            action_delete = QAction("删除按钮", self)
            action_delete.triggered.connect(lambda: self._on_delete_button(data.get("id"), data.get("label")))
            menu.addAction(action_delete)

            action_rename = QAction("重命名按钮", self)
            action_rename.triggered.connect(lambda: self._on_rename_button(data.get("id"), data.get("label")))
            menu.addAction(action_rename)

            menu.addSeparator()

            # 按钮特有操作 - 脚本绑定
            action_bind = QAction("绑定脚本...", self)
            action_bind.triggered.connect(lambda: self._on_bind_script(data.get("id")))
            menu.addAction(action_bind)

            # Show unbind option if currently bound
            if data.get("script_id"):
                action_unbind = QAction("解除绑定", self)
                action_unbind.triggered.connect(lambda: self._on_unbind_script(data.get("id")))
                menu.addAction(action_unbind)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _on_add_tab(self):
        """Add new tab - creates ribbon_tabs record, NOT a script."""
        text, ok = QInputDialog.getText(self, "添加 Tab", "输入 Tab 名称:")
        if ok and text.strip():
            tab_name = text.strip()
            tab_id = self.wps_service.add_tab(tab_name, self.current_app)
            self.current_tab_id = tab_id
            self.current_tab_name = tab_name
            # Auto-create a default group
            self.wps_service.add_group("默认分组", tab_id, self.current_app)
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_rename_tab(self, tab_id, tab_name):
        """Rename a tab."""
        text, ok = QInputDialog.getText(self, "重命名 Tab", "输入新名称:", text=tab_name)
        if ok and text.strip():
            new_name = text.strip()
            self.wps_service.update_tab(tab_id, new_name)
            self.current_tab_name = new_name
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_delete_tab(self, tab_id, tab_name):
        """Delete a tab and all its groups/buttons."""
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除 Tab「{tab_name}」及其所有分组和按钮吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.wps_service.delete_tab(tab_id)
            # Select another tab or clear
            remaining = self.wps_service.get_all_tabs(self.current_app)
            if remaining:
                self.current_tab_id = remaining[0]["id"]
                self.current_tab_name = remaining[0]["name"]
            else:
                self.current_tab_id = None
                self.current_tab_name = None
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_add_group(self, tab_id):
        """Add new group to current tab."""
        text, ok = QInputDialog.getText(self, "新增分组", "输入分组名称:")
        if ok and text.strip():
            group_name = text.strip()
            self.wps_service.add_group(group_name, tab_id, self.current_app)
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_rename_group(self, group_id, group_name):
        """Rename a group."""
        text, ok = QInputDialog.getText(self, "重命名分组", "输入新名称:", text=group_name)
        if ok and text.strip():
            self.wps_service.update_group(group_id, text.strip())
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_delete_group(self, group_id, group_name):
        """Delete a group and all its buttons."""
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除分组「{group_name}」及其所有按钮吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.wps_service.delete_group(group_id)
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_add_button(self, group_id):
        """Add new button to group - creates ribbon_buttons record, NOT a script."""
        text, ok = QInputDialog.getText(self, "新增按钮", "输入按钮标签:")
        if ok and text.strip():
            button_label = text.strip()
            self.wps_service.add_button(button_label, group_id, self.current_app)
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_rename_button(self, button_id, button_label):
        """Rename a button."""
        text, ok = QInputDialog.getText(self, "重命名按钮", "输入按钮标签:", text=button_label)
        if ok and text.strip():
            self.wps_service.update_button(button_id, text.strip())
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_delete_button(self, button_id, button_label):
        """Delete a button."""
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除按钮「{button_label}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.wps_service.delete_button(button_id)
            self.refresh_all()
            self.main_module.refresh_preview()

    def _on_bind_script(self, button_id):
        """Bind an existing script to this button."""
        # Get all scripts for selection
        all_scripts = self.wps_service.get_all_scripts(self.current_app)

        if not all_scripts:
            QMessageBox.information(self, "提示", "没有可用的脚本，请先在脚本列表中新增脚本")
            return

        # Build selection list: name | main_function | binding status
        items = []
        for s in all_scripts:
            name = s.get("name", "未命名")
            main_func = s.get("main_function", "") or "无功能描述"

            # Check if this script is already bound to any button
            buttons = self.wps_service.get_all_buttons(target_app=self.current_app)
            bound_to = None
            for btn in buttons:
                if btn.get("script_id") == s.get("id"):
                    # Get button's group and tab info
                    btn_info = self.wps_service.get_button_with_script(btn["id"])
                    if btn_info:
                        bound_to = f"[已绑定: {btn['label']}]"
                    break

            binding = bound_to or "未绑定"
            items.append(f"{name} | {main_func} | {binding}")

        item, ok = QInputDialog.getItem(self, "绑定脚本", "选择脚本:", items, 0, False)
        if ok and item:
            # Extract script name
            script_name = item.split(" | ")[0]

            # Find selected script
            selected_script = None
            for s in all_scripts:
                if s.get("name") == script_name:
                    selected_script = s
                    break

            if selected_script:
                # Bind script to button
                self.wps_service.bind_script(button_id, selected_script["id"])
                QMessageBox.information(self, "成功",
                    f"已将脚本「{script_name}」绑定到此按钮")
                self.refresh_all()
                self.main_module._refresh_all()

    def _on_unbind_script(self, button_id):
        """Unbind script from this button."""
        reply = QMessageBox.question(self, "解除绑定",
            "确定要解除此按钮的脚本绑定吗？按钮将保留，但不再执行脚本。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.wps_service.bind_script(button_id, None)  # None to unbind
            self.refresh_all()


# ===== JSA Macro Panel =====

class JsaMacroPanel(QWidget):
    """Panel for browsing JSA macro code (read-only)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_script_id = None
        self.wps_service = None
        self._setup_ui()

    def set_wps_service(self, service):
        """Set the WPS service for saving."""
        self.wps_service = service

    def _setup_ui(self):
        """Set up the panel UI with toolbar and editor."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header row - 标题和工具栏
        header_layout = QHBoxLayout()

        header = QLabel("JSA宏代码浏览区")
        header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 13px;
                padding: 5px 0;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()

        # JSA宏代码浏览区标签 (只读，编辑请通过脚本列表"编辑"按钮)
        browser_hint = QLabel('（编辑请通过脚本列表中的"编辑"按钮）')
        browser_hint.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                padding: 0 5px;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(browser_hint)

        layout.addLayout(header_layout)

        # 代码编辑器 - 只读浏览模式
        self.code_editor = QPlainTextEdit()
        self.code_editor.setReadOnly(True)
        self.code_editor.setFont(QFont("Consolas", 11))
        self.code_editor.setPlaceholderText('// 选择脚本后在此浏览JSA宏代码\n// 编辑请使用脚本列表中的"编辑"按钮')
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background-color: #FEFEFE;
                line-height: 1.4;
            }
        """)
        # textChanged signal not needed - editor is read-only browsing
        layout.addWidget(self.code_editor)

        # 设置语法高亮器
        self.highlighter = JsaSyntaxHighlighter(self.code_editor.document())

        self.setLayout(layout)

    def load_script(self, script):
        """Load JSA code from script data."""
        self.current_script_id = script.get("id")
        js_code = script.get("js_code", "") or script.get("vba_code", "")
        self.code_editor.setPlainText(js_code)

    def get_code(self):
        """Get the JSA code from editor."""
        return self.code_editor.toPlainText()

    def clear(self):
        """Clear editor."""
        self.current_script_id = None
        self.code_editor.clear()


# ===== Script Dialog =====

class ScriptDialog(QDialog):
    """Dialog for creating a new script (only script info, no ribbon config)."""

    def __init__(self, parent=None, script_data=None, default_app="word"):
        super().__init__(parent)
        self.script_data = script_data
        self.default_app = default_app
        self.is_edit_mode = script_data is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("编辑脚本" if self.is_edit_mode else "新增脚本")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Name - 透明标签样式
        name_layout = QHBoxLayout()
        name_label = QLabel("脚本名称:")
        name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 13px;
            }
        """)
        name_label.setFixedWidth(80)
        name_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("脚本名称（用于Ribbon onAction）")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Main function - 透明标签样式
        func_layout = QHBoxLayout()
        func_label = QLabel("主要功能:")
        func_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 13px;
            }
        """)
        func_label.setFixedWidth(80)
        func_layout.addWidget(func_label)

        self.function_input = QLineEdit()
        self.function_input.setPlaceholderText("简述脚本的主要功能")
        func_layout.addWidget(self.function_input)
        layout.addLayout(func_layout)

        # JSA code
        code_group = QGroupBox("JSA 宏代码")
        code_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        code_layout = QVBoxLayout()

        code_tip = QLabel("提示：代码将作为 JSA 函数体直接写入，支持标准 JSA 语法")
        code_tip.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        code_layout.addWidget(code_tip)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setTabStopDistance(40)  # 4 spaces worth
        self.code_editor.setPlaceholderText("// 输入 JSA 代码...\nfunction myScript() {\n    MsgBox('Hello World');\n}")
        code_layout.addWidget(self.code_editor)

        code_group.setLayout(code_layout)
        layout.addWidget(code_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setFixedWidth(100)
        self.save_btn.setDefault(True)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #006cbd;
            }
        """)
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_data(self):
        """Load existing script data for edit mode."""
        if self.is_edit_mode and self.script_data:
            self.name_input.setText(self.script_data.get("name", ""))
            self.function_input.setText(self.script_data.get("main_function", ""))
            js_code = self.script_data.get("js_code", "") or self.script_data.get("vba_code", "")
            self.code_editor.setPlainText(js_code)

    def _on_save(self):
        """Handle save button click."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入脚本名称")
            return

        code = self.code_editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "警告", "请输入 JSA 宏代码")
            return

        self.accept()

    def get_script_data(self):
        """Get the script data from the dialog."""
        return {
            "name": self.name_input.text().strip(),
            "main_function": self.function_input.text().strip(),
            "js_code": self.code_editor.toPlainText()
        }


# ===== Main WpsModule =====

class WpsModule(QWidget):
    """WPS script management module with Ribbon Builder."""

    script_added = pyqtSignal()
    script_deleted = pyqtSignal()
    script_updated = pyqtSignal()

    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db_path = db_path

        self.wps_service = WpsService(db_path)

        self.templates_dir = None
        self.word_startup = None
        self.excel_startup = None
        self.deployment_service = None

        self._setup_ui()
        self._refresh_all()

    def set_paths(self, templates_dir: str, word_startup: str = None, excel_startup: str = None):
        """Set the paths for template and startup directories."""
        self.templates_dir = templates_dir
        self.word_startup = word_startup
        self.excel_startup = excel_startup
        self.wps_service.set_paths(templates_dir, word_startup, excel_startup)

    def _setup_ui(self):
        """Set up the module UI with horizontal preview layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)

        # ===== Row 1: App selector (Word/Excel) =====
        app_layout = QHBoxLayout()

        # 应用选择标签 - 透明无边框
        app_label = QLabel("应用:")
        app_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        app_layout.addWidget(app_label)

        self.word_btn = QPushButton("Word")
        self.word_btn.setFixedSize(70, 32)
        self.word_btn.setCheckable(True)
        self.word_btn.setChecked(True)
        self.word_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #DADDEA;
                border-radius: 8px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:checked {
                background-color: #5B5BD6;
                color: white;
                border-color: #5B5BD6;
            }
            QPushButton:!checked {
                background-color: #FFFFFF;
                color: #555A70;
            }
        """)
        self.word_btn.clicked.connect(self._on_word_clicked)
        app_layout.addWidget(self.word_btn)

        self.excel_btn = QPushButton("Excel")
        self.excel_btn.setFixedSize(70, 32)
        self.excel_btn.setCheckable(True)
        self.excel_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #DADDEA;
                border-radius: 8px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:checked {
                background-color: #5B5BD6;
                color: white;
                border-color: #5B5BD6;
            }
            QPushButton:!checked {
                background-color: #FFFFFF;
                color: #555A70;
            }
        """)
        self.excel_btn.clicked.connect(self._on_excel_clicked)
        app_layout.addWidget(self.excel_btn)

        app_layout.addSpacing(12)

        # Deploy button
        self.deploy_btn = QPushButton("一键部署")
        self.deploy_btn.setFixedSize(90, 32)
        set_button_variant(self.deploy_btn, "primary")
        self.deploy_btn.clicked.connect(self._on_deploy)
        app_layout.addWidget(self.deploy_btn)

        app_layout.addStretch()
        layout.addLayout(app_layout)

        # ===== Row 2: Ribbon Preview (horizontal bar) =====
        preview_container = QFrame()
        preview_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E3E6EF;
                border-radius: 9px;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        # 功能区预览标签 - 紧凑样式
        preview_title = QLabel("功能区预览")
        preview_title.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #73778A;
                padding: 6px 10px;
                background: transparent;
                border: none;
            }
        """)
        preview_layout.addWidget(preview_title)

        self.ribbon_preview = RibbonPreviewView()
        preview_layout.addWidget(self.ribbon_preview)

        preview_container.setLayout(preview_layout)
        preview_container.setFixedHeight(95)
        layout.addWidget(preview_container)

        # ===== Row 3: Main content - Left (Ribbon Tree) + Right (Script Manager) =====
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel - Ribbon Tree
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E3E6EF;
                border-radius: 9px;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(7)

        # 功能区结构标签 - 透明
        tree_title = QLabel("功能区结构")
        tree_title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333;
                background: transparent;
                border: none;
                padding: 2px 0;
            }
        """)
        left_layout.addWidget(tree_title)

        self.ribbon_tree = RibbonTreePanel(main_module=self)
        self.ribbon_tree.set_wps_service(self.wps_service)
        left_layout.addWidget(self.ribbon_tree)

        left_panel.setLayout(left_layout)

        # Right Panel - Script Manager
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E3E6EF;
                border-radius: 9px;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(8)

        # Script list header
        script_header = QHBoxLayout()

        # 脚本列表标签 - 透明
        script_title = QLabel("脚本列表")
        script_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                background: transparent;
                border: none;
            }
        """)
        script_header.addWidget(script_title)

        script_header.addStretch()

        # Add script button
        self.add_script_btn = QPushButton("+ 新增脚本")
        self.add_script_btn.setFixedHeight(30)
        set_button_variant(self.add_script_btn, "primary")
        self.add_script_btn.clicked.connect(self._on_add_script)
        script_header.addWidget(self.add_script_btn)

        # Delete script button
        self.delete_script_btn = QPushButton("删除")
        self.delete_script_btn.setFixedHeight(30)
        set_button_variant(self.delete_script_btn, "danger")
        self.delete_script_btn.clicked.connect(self._on_delete_script)
        script_header.addWidget(self.delete_script_btn)

        # Edit script button
        self.edit_script_btn = QPushButton("编辑")
        self.edit_script_btn.setFixedHeight(30)
        self.edit_script_btn.clicked.connect(self._on_edit_script)
        script_header.addWidget(self.edit_script_btn)

        right_layout.addLayout(script_header)

        # Script list
        self.script_list = QListWidget()
        self.script_list.setAlternatingRowColors(True)
        self.script_list.itemSelectionChanged.connect(self._on_script_selected)
        right_layout.addWidget(self.script_list, 1)

        # JSA Macro Editor
        self.jsa_macro_panel = JsaMacroPanel()
        self.jsa_macro_panel.set_wps_service(self.wps_service)
        right_layout.addWidget(self.jsa_macro_panel, 2)

        right_panel.setLayout(right_layout)

        # Set up splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        layout.addWidget(main_splitter)
        self.setLayout(layout)

    def _refresh_all(self):
        """Refresh all UI components."""
        app = "word" if self.word_btn.isChecked() else "excel"
        self.ribbon_tree.set_app(app)
        self.ribbon_tree.refresh_all()
        self._refresh_script_list()
        self.refresh_preview()

    def _refresh_script_list(self):
        """Refresh the script list with detailed info.

        显示所有脚本，包括：
        - 脚本名称
        - 主要功能
        - 绑定的按钮位置（从 ribbon_buttons 查询）
        """
        self.script_list.clear()
        app = "word" if self.word_btn.isChecked() else "excel"
        scripts = self.wps_service.get_all_scripts(app)

        # Get all buttons with their script bindings to show binding info
        all_buttons = self.wps_service.get_all_buttons(target_app=app)
        script_bindings = {}  # script_id -> list of button info

        for btn in all_buttons:
            if btn.get("script_id"):
                script_id = btn["script_id"]
                if script_id not in script_bindings:
                    script_bindings[script_id] = []
                # Get group and tab info for this button
                group = self.wps_service.get_group(btn["group_id"])
                if group:
                    tab = self.wps_service.get_tab(group.get("tab_id"))
                    if tab:
                        script_bindings[script_id].append({
                            "tab": tab["name"],
                            "group": group["name"],
                            "label": btn["label"]
                        })

        for script in scripts:
            name = script.get("name", "未命名")
            main_func = script.get("main_function", "") or "无功能描述"

            # 显示绑定的按钮信息（从 ribbon_buttons 查询）
            script_id = script.get("id")
            bindings = script_bindings.get(script_id, [])

            # 构建显示文本
            display_lines = []
            display_lines.append(f"名称: {name}")
            display_lines.append(f"功能: {main_func}")

            # 绑定信息
            if bindings:
                binding_strs = [f"[{b['tab']} > {b['group']} > {b['label']}]" for b in bindings]
                display_lines.append(f"绑定: {', '.join(binding_strs)}")
            else:
                display_lines.append("绑定: 未绑定按钮")

            display = "\n".join(display_lines)

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, script["id"])
            # 设置高度以适应多行文本
            item.setSizeHint(QSize(0, 70))
            self.script_list.addItem(item)

    def refresh_preview(self):
        """Refresh ribbon preview from structure tables."""
        if not self.ribbon_tree.current_tab_id:
            self.ribbon_preview.clear_preview()
            return

        # Get groups and buttons from structure tables
        groups = self.wps_service.get_all_groups(self.ribbon_tree.current_tab_id)

        groups_with_buttons = []
        for group in groups:
            buttons = self.wps_service.get_all_buttons(group["id"])
            button_labels = [btn["label"] for btn in buttons]
            groups_with_buttons.append((group["name"], button_labels))

        self.ribbon_preview.clear_preview()
        if groups_with_buttons:
            self.ribbon_preview.show_tab_preview(self.ribbon_tree.current_tab_name, groups_with_buttons)

    def show_tab_preview(self, tab_name):
        """Show preview for a specific tab."""
        self.ribbon_tree.current_tab_name = tab_name
        self.refresh_preview()

    def load_script_in_editor(self, script):
        """Load a script in the JSA browser."""
        self.jsa_macro_panel.load_script(script)

    def _on_script_selected(self):
        """Handle script selection from list."""
        current_row = self.script_list.currentRow()
        if current_row < 0:
            return

        script_id = self.script_list.item(current_row).data(Qt.ItemDataRole.UserRole)
        script = self.wps_service.get_script(script_id)
        if script:
            self.jsa_macro_panel.load_script(script)

    def _on_word_clicked(self):
        """Handle Word button click."""
        self.word_btn.setChecked(True)
        self.excel_btn.setChecked(False)
        self._refresh_all()

    def _on_excel_clicked(self):
        """Handle Excel button click."""
        self.word_btn.setChecked(False)
        self.excel_btn.setChecked(True)
        self._refresh_all()

    def _on_deploy(self):
        """Handle deploy button click — deploy templates for current app."""
        if not self.deployment_service:
            QMessageBox.warning(self, "提示", "部署服务未初始化，请先配置路径。")
            return
        # Refresh deployment service template dirs from current module state
        if self.word_startup:
            self.deployment_service.word_template_dir = self.word_startup
        if self.excel_startup:
            self.deployment_service.excel_template_dir = self.excel_startup
        app = "word" if self.word_btn.isChecked() else "excel"
        reply = QMessageBox.question(
            self, "确认部署",
            f"即将部署 {app.upper()} 的功能区配置和模板，确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            result = self.deployment_service.deploy_all()
            if result.get("success"):
                QMessageBox.information(self, "部署成功", result.get("message", "部署完成"))
            else:
                errors = result.get("errors", ["未知错误"])
                QMessageBox.warning(self, "部署失败", "\n".join(errors))
        except Exception as e:
            QMessageBox.critical(self, "部署错误", str(e))

    def _on_app_changed(self, index):
        """Handle app change (deprecated)."""
        self._refresh_all()

    def _on_add_script(self):
        """Handle add script button click.

        用户创建脚本时不绑定功能区位置，之后通过按钮的"绑定脚本"功能来绑定。
        """
        app = "word" if self.word_btn.isChecked() else "excel"

        dialog = ScriptDialog(self, default_app=app)
        if dialog.exec():
            script_data = dialog.get_script_data()
            self.wps_service.add_script(
                name=script_data["name"],
                js_code=script_data["js_code"],
                target_app=app,
                main_function=script_data["main_function"]
            )
            self._refresh_all()
            self.script_added.emit()

    def _on_edit_script(self):
        """Handle edit script button click - opens ScriptDialog in edit mode."""
        selected_items = self.script_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要编辑的脚本")
            return

        item = selected_items[0]
        script_id = item.data(Qt.ItemDataRole.UserRole)
        if not script_id:
            return

        script = self.wps_service.get_script(script_id)
        if not script:
            QMessageBox.warning(self, "警告", "脚本不存在")
            return

        dialog = ScriptDialog(self, script_data=script)
        if dialog.exec():
            script_data = dialog.get_script_data()
            self.wps_service.update_script(
                script_id,
                name=script_data["name"],
                js_code=script_data["js_code"],
                main_function=script_data["main_function"],
            )
            self._refresh_all()
            self.script_added.emit()

    def _on_delete_script(self):
        """Handle delete script button click."""
        current_row = self.script_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个脚本")
            return

        script_id = self.script_list.item(current_row).data(Qt.ItemDataRole.UserRole)
        script = self.wps_service.get_script(script_id)
        if not script:
            return

        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除脚本「{script.get('name')}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.wps_service.delete_script(script_id)
            self.jsa_macro_panel.clear()
            self._refresh_all()
            self.script_deleted.emit()
