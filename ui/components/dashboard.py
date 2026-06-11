"""Dashboard for the ScriptNexus workspace."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame


class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard")
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget#dashboard { background: #F5F6FA; }
            QLabel#eyebrow { color: #5B5BD6; font-size: 11px; font-weight: 700; }
            QLabel#dashboardTitle { color: #202333; font-size: 26px; font-weight: 700; }
            QLabel#dashboardLead { color: #74788B; font-size: 13px; }
            QFrame[card="true"] { background: #FFFFFF; border: 1px solid #E3E6EF; border-radius: 12px; }
            QLabel[cardTitle="true"] { color: #777B8D; font-size: 12px; font-weight: 600; }
            QLabel[cardCount="true"] { color: #2B2E3E; font-size: 34px; font-weight: 700; }
            QLabel[cardHint="true"] { color: #A0A3B2; font-size: 10px; }
            QFrame#guidePanel { background: #EEEEFF; border: 1px solid #DEDEFA; border-radius: 12px; }
            QLabel#guideTitle { color: #3E3E9D; font-size: 15px; font-weight: 700; }
            QLabel#guideText { color: #66669A; font-size: 12px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 34, 38, 32)
        layout.setSpacing(8)
        eyebrow = QLabel("SCRIPTNEXUS WORKSPACE")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("欢迎回来")
        title.setObjectName("dashboardTitle")
        layout.addWidget(title)
        lead = QLabel("从一个清晰的工作台管理脚本、自动化任务与部署状态。")
        lead.setObjectName("dashboardLead")
        layout.addWidget(lead)
        layout.addSpacing(24)

        cards = QHBoxLayout()
        cards.setSpacing(16)
        self.python_card = self._create_stat_card("Python 脚本", "python_count", "本地自动化任务")
        self.wps_card = self._create_stat_card("WPS 脚本", "wps_count", "Office 宏与功能区")
        self.js_card = self._create_stat_card("Chrome JS", "js_count", "浏览器书签脚本")
        cards.addWidget(self.python_card)
        cards.addWidget(self.wps_card)
        cards.addWidget(self.js_card)
        layout.addLayout(cards)
        layout.addSpacing(20)

        guide = QFrame()
        guide.setObjectName("guidePanel")
        guide_layout = QVBoxLayout(guide)
        guide_layout.setContentsMargins(20, 16, 20, 16)
        guide_layout.setSpacing(5)
        guide_title = QLabel("开始工作")
        guide_title.setObjectName("guideTitle")
        guide_text = QLabel("从左侧选择脚本类型。你可以新增、编辑、运行或部署现有脚本。")
        guide_text.setObjectName("guideText")
        guide_layout.addWidget(guide_title)
        guide_layout.addWidget(guide_text)
        layout.addWidget(guide)
        layout.addStretch()

    @staticmethod
    def _create_stat_card(title, count_name, hint):
        card = QFrame()
        card.setProperty("card", True)
        card.setMinimumHeight(154)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setProperty("cardTitle", True)
        count_label = QLabel("0")
        count_label.setObjectName(count_name)
        count_label.setProperty("cardCount", True)
        hint_label = QLabel(hint)
        hint_label.setProperty("cardHint", True)
        card_layout.addWidget(title_label)
        card_layout.addWidget(count_label)
        card_layout.addStretch()
        card_layout.addWidget(hint_label)
        return card

    def update_stats(self, python_count, wps_count, js_count):
        self._update_card_count(self.python_card, "python_count", python_count)
        self._update_card_count(self.wps_card, "wps_count", wps_count)
        self._update_card_count(self.js_card, "js_count", js_count)

    @staticmethod
    def _update_card_count(card, object_name, count):
        count_label = card.findChild(QLabel, object_name)
        if count_label:
            count_label.setText(str(count))
