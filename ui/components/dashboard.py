"""Dashboard - Home page dashboard for the main window."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt


class Dashboard(QWidget):
    """Dashboard page with welcome title and statistics cards.

    Features:
        - Welcome title
        - Three statistics cards: Python Scripts, WPS Scripts, Chrome JS Scripts
    """

    def __init__(self, parent=None):
        """Initialize the dashboard.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dashboard UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Welcome title
        self.welcome_label = QLabel("欢迎使用脚本管理器")
        self.welcome_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
        """)
        layout.addWidget(self.welcome_label)

        # Add spacing
        layout.addSpacing(20)

        # Statistics cards container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Python Scripts card
        self.python_card = self._create_stat_card("Python 脚本", "python_count", 0)
        cards_layout.addWidget(self.python_card)

        # WPS Scripts card
        self.wps_card = self._create_stat_card("WPS 脚本", "wps_count", 0)
        cards_layout.addWidget(self.wps_card)

        # Chrome JS Scripts card
        self.js_card = self._create_stat_card("Chrome JS脚本", "js_count", 0)
        cards_layout.addWidget(self.js_card)

        layout.addLayout(cards_layout)
        layout.addStretch()

        self.setLayout(layout)

    def _create_stat_card(self, title, count_name, count):
        """Create a statistics card.

        Args:
            title: Card title
            count_name: Object name for the count label
            count: Initial count value

        Returns:
            QFrame instance containing the card
        """
        card = QFrame()
        card.setFixedHeight(150)
        card.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(10)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)

        # Count label
        count_label = QLabel(str(count))
        count_label.setObjectName(count_name)
        count_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #0078D4;
            }
        """)
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(count_label)

        card.setLayout(card_layout)
        return card

    def update_stats(self, python_count, wps_count, js_count):
        """Update the statistics cards with new counts.

        Args:
            python_count: Number of Python scripts
            wps_count: Number of WPS scripts
            js_count: Number of JS scripts
        """
        # Update each card using its object name
        self._update_card_count(self.python_card, "python_count", python_count)
        self._update_card_count(self.wps_card, "wps_count", wps_count)
        self._update_card_count(self.js_card, "js_count", js_count)

    def _update_card_count(self, card, object_name, count):
        """Update the count label of a card.

        Args:
            card: QFrame card containing the count label
            object_name: Object name of the count label
            count: New count value
        """
        count_label = card.findChild(QLabel, object_name)
        if count_label:
            count_label.setText(str(count))
