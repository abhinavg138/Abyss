from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QFrame,
)

from ui.styles.theme import STYLE


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("🌌 Abyss")

        self.resize(1600, 900)

        self.setMinimumSize(1200, 700)

        self.setStyleSheet(STYLE)

        self.build_ui()

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        root.setContentsMargins(0, 0, 0, 0)

        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        root.addWidget(splitter)

        ####################################################
        # LEFT SIDEBAR
        ####################################################

        sidebar = QFrame()

        sidebar.setFixedWidth(260)

        sidebar.setStyleSheet("""
        background:#111827;
        border-right:1px solid #30363D;
        """)

        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.setContentsMargins(20,20,20,20)

        logo = QLabel("🌌  ABYSS")

        logo.setStyleSheet("""
        font-size:24px;
        font-weight:bold;
        color:white;
        """)

        sidebar_layout.addWidget(logo)

        sidebar_layout.addSpacing(20)

        new_chat = QPushButton("+  New Chat")

        sidebar_layout.addWidget(new_chat)

        sidebar_layout.addSpacing(20)

        chats = QListWidget()

        chats.addItem("Welcome")

        chats.addItem("Memory Test")

        chats.addItem("Python Project")

        chats.addItem("GUI Design")

        chats.setStyleSheet("""
        QListWidget{
            background:#161B22;
            border:none;
            border-radius:10px;
        }

        QListWidget::item{
            padding:10px;
        }

        QListWidget::item:selected{
            background:#7C3AED;
        }
        """)

        sidebar_layout.addWidget(chats)

        sidebar_layout.addStretch()

        memory = QPushButton("🧠 Memory")

        tools = QPushButton("🛠 Tools")

        settings = QPushButton("⚙ Settings")

        sidebar_layout.addWidget(memory)

        sidebar_layout.addWidget(tools)

        sidebar_layout.addWidget(settings)

        ####################################################
        # CENTER
        ####################################################

        center = QWidget()

        center_layout = QVBoxLayout(center)

        center_layout.setContentsMargins(20,20,20,20)

        center_layout.setSpacing(15)

        ####################################################
        # TOP BAR
        ####################################################

        top = QHBoxLayout()

        title = QLabel("Abyss")

        title.setStyleSheet("""
        font-size:24px;
        font-weight:bold;
        """)

        top.addWidget(title)

        top.addStretch()

        provider = QPushButton("Groq ▼")

        provider.setFixedWidth(140)

        top.addWidget(provider)

        center_layout.addLayout(top)

        ####################################################
        # CHAT
        ####################################################

        self.chat = QTextEdit()

        self.chat.setReadOnly(True)

        self.chat.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.chat.setHtml("""

<h2>Welcome to Abyss</h2>

<p>Your personal AI assistant.</p>

<hr>

<b>You</b>

<p>Hello!</p>

<br>

<b>Abyss</b>

<p>Hi Abhinav 👋</p>

<p>Ready to build something awesome today?</p>

""")

        center_layout.addWidget(self.chat)

        ####################################################
        # INPUT
        ####################################################

        bottom = QHBoxLayout()

        attach = QPushButton("📎")

        attach.setFixedWidth(45)

        bottom.addWidget(attach)

        self.input = QTextEdit()

        self.input.setMaximumHeight(70)

        self.input.setPlaceholderText(
            "Type your message..."
        )

        bottom.addWidget(self.input)

        send = QPushButton("➤")

        send.setFixedWidth(60)

        bottom.addWidget(send)

        center_layout.addLayout(bottom)

        ####################################################
        # RIGHT PANEL
        ####################################################

        right = QFrame()

        right.setFixedWidth(280)

        right.setStyleSheet("""
        background:#111827;
        border-left:1px solid #30363D;
        """)

        right_layout = QVBoxLayout(right)

        right_layout.setContentsMargins(20,20,20,20)

        right_layout.addWidget(QLabel("Workspace"))

        files = QListWidget()

        files.addItems([
            "assistant/",
            "memory/",
            "providers/",
            "tools/",
            "",
            "manager.py",
            "router.py",
            "config.py",
            "app.py"
        ])

        files.setStyleSheet("""
        QListWidget{
            background:#161B22;
            border:none;
            border-radius:10px;
        }

        QListWidget::item{
            padding:8px;
        }
        """)

        right_layout.addWidget(files)

        splitter.addWidget(sidebar)

        splitter.addWidget(center)

        splitter.addWidget(right)

        splitter.setStretchFactor(1,5)

        ####################################################
        # STATUS BAR
        ####################################################

        status = QStatusBar()

        self.setStatusBar(status)

        status.showMessage(
            "🟢 Connected   |   Groq   |   Memory Active"
        )