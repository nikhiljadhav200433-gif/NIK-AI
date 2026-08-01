from __future__ import annotations

import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
)

# ============================================================
# EASY EDIT AREA — CHANGE YOUR UI HERE
# ============================================================

APP_NAME = "NIK AI"
ASSISTANT_NAME = "NIK"
OWNER_NAME = "Nikhil"
TAGLINE = "Neural Intelligence Kernel"
WINDOW_TITLE = "NIK AI — Nikhil"

SIDEBAR_TITLE = "🤖 NIK AI"
WELCOME_MESSAGE = "Hello Nikhil. I am NIK. How can I help you today?"
SETUP_TITLE = "Set up NIK AI"
FOOTER_TEXT = "© Nikhil AI Lab"

# Change colors here
COLOR_BG = "#0b0f19"
COLOR_SIDEBAR = "#0f172a"
COLOR_PANEL = "#111827"
COLOR_PANEL2 = "#1f2937"
COLOR_BORDER = "#263244"
COLOR_TEXT = "#e5e7eb"
COLOR_DIM = "#9ca3af"
COLOR_ACCENT = "#38bdf8"
COLOR_GREEN = "#22c55e"
COLOR_RED = "#ef4444"
COLOR_USER_BUBBLE = "#2563eb"
COLOR_AI_BUBBLE = "#1f2937"

# Window size
DEFAULT_WIDTH = 1050
DEFAULT_HEIGHT = 720
MIN_WIDTH = 850
MIN_HEIGHT = 560

# ============================================================
# DO NOT EDIT BELOW UNLESS YOU KNOW PYQT
# ============================================================

_OS = platform.system()


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"


class ChatBubble(QFrame):
    def __init__(self, text: str, role: str = "ai"):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)

        bubble = QFrame()
        bubble.setMaximumWidth(650)

        bg = COLOR_USER_BUBBLE if role == "user" else COLOR_AI_BUBBLE
        border = COLOR_ACCENT if role == "user" else COLOR_BORDER

        bubble.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 16px;
            }}
        """)

        lay = QVBoxLayout(bubble)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        name = QLabel("You" if role == "user" else ASSISTANT_NAME)
        name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {COLOR_ACCENT if role != 'user' else '#dbeafe'}; background: transparent; border: none;")
        lay.addWidget(name)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setFont(QFont("Segoe UI", 10))
        msg.setStyleSheet(f"color: {COLOR_TEXT}; background: transparent; border: none;")
        lay.addWidget(msg)

        if role == "user":
            outer.addStretch()
            outer.addWidget(bubble)
        else:
            outer.addWidget(bubble)
            outer.addStretch()


class ChatArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QScrollArea {{
                background: {COLOR_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLOR_BG};
                width: 10px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_PANEL2};
                border-radius: 5px;
            }}
        """)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(2)
        self.layout.addStretch()
        self.setWidget(self.container)

    def add_message(self, text: str, role: str = "ai"):
        self.layout.insertWidget(self.layout.count() - 1, ChatBubble(text, role))
        QTimer.singleShot(40, self._scroll_bottom)

    def _scroll_bottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class SetupOverlay(QWidget):
    done = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sel_os = {"Windows": "windows", "Darwin": "mac", "Linux": "linux"}.get(_OS, "windows")
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 18px;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 26, 30, 26)
        lay.setSpacing(12)

        title = QLabel(SETUP_TITLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{COLOR_TEXT}; background:transparent; border:none;")
        lay.addWidget(title)

        subtitle = QLabel("Enter your API keys once. They will be saved locally.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet(f"color:{COLOR_DIM}; background:transparent; border:none;")
        lay.addWidget(subtitle)

        self._key = self._input("Gemini API key")
        self._or = self._input("OpenRouter API key")
        lay.addWidget(self._key)
        lay.addWidget(self._or)

        btn = QPushButton("Continue")
        btn.setFixedHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT};
                color: #001018;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{ background: #7dd3fc; }}
        """)
        btn.clicked.connect(self._submit)
        lay.addWidget(btn)

    def _input(self, placeholder: str):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setEchoMode(QLineEdit.EchoMode.Password)
        e.setFixedHeight(42)
        e.setFont(QFont("Segoe UI", 10))
        e.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_BG};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 12px;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACCENT}; }}
        """)
        return e

    def _submit(self):
        key = self._key.text().strip()
        or_key = self._or.text().strip()
        if key and or_key:
            self.done.emit(key, or_key, self._sel_os)


class MainWindow(QMainWindow):
    _log_sig = pyqtSignal(str)
    _state_sig = pyqtSignal(str)

    def __init__(self, face_path: str = ""):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        self.on_text_command = None
        self._muted = False
        self._current_file: str | None = None
        self._state = "READY"

        central = QWidget()
        central.setStyleSheet(f"background:{COLOR_BG};")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._sidebar())

        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._topbar())
        self.chat = ChatArea()
        main.addWidget(self.chat, stretch=1)
        main.addWidget(self._composer())

        root.addLayout(main, stretch=1)

        self._log_sig.connect(self._receive_log)
        self._state_sig.connect(self._apply_state)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

        self._ready = self._check_config()
        self._overlay = None
        if not self._ready:
            self._show_setup()
        else:
            self.chat.add_message(WELCOME_MESSAGE, "ai")

        QShortcut(QKeySequence("F4"), self).activated.connect(self._toggle_mute)
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)

    def _sidebar(self):
        w = QWidget()
        w.setFixedWidth(245)
        w.setStyleSheet(f"background:{COLOR_SIDEBAR}; border-right:1px solid {COLOR_BORDER};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        logo = QLabel(SIDEBAR_TITLE)
        logo.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{COLOR_TEXT};")
        lay.addWidget(logo)

        sub = QLabel(TAGLINE)
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet(f"color:{COLOR_DIM};")
        lay.addWidget(sub)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{COLOR_BORDER};")
        lay.addWidget(line)

        self._status_card = QLabel("● READY")
        self._status_card.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._status_card.setStyleSheet(f"""
            QLabel {{
                color:{COLOR_GREEN};
                background:{COLOR_PANEL};
                border:1px solid {COLOR_BORDER};
                border-radius:14px;
                padding:14px;
            }}
        """)
        lay.addWidget(self._status_card)

        self._file_label = QLabel("No file uploaded")
        self._file_label.setWordWrap(True)
        self._file_label.setFont(QFont("Segoe UI", 9))
        self._file_label.setStyleSheet(f"""
            QLabel {{
                color:{COLOR_DIM};
                background:{COLOR_PANEL};
                border:1px solid {COLOR_BORDER};
                border-radius:14px;
                padding:14px;
            }}
        """)
        lay.addWidget(self._file_label)

        tips = QLabel("Shortcuts\n\nF4  Toggle microphone\nF11 Fullscreen\n\nUse text, voice, or file upload.")
        tips.setFont(QFont("Segoe UI", 9))
        tips.setStyleSheet(f"color:{COLOR_DIM}; padding:10px;")
        tips.setWordWrap(True)
        lay.addWidget(tips)

        lay.addStretch()

        credit = QLabel(FOOTER_TEXT)
        credit.setFont(QFont("Segoe UI", 8))
        credit.setStyleSheet(f"color:{COLOR_DIM};")
        lay.addWidget(credit)

        return w

    def _topbar(self):
        w = QWidget()
        w.setFixedHeight(66)
        w.setStyleSheet(f"background:{COLOR_BG}; border-bottom:1px solid {COLOR_BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(22, 0, 22, 0)

        title = QLabel("New Chat")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{COLOR_TEXT};")
        lay.addWidget(title)

        lay.addStretch()

        self._clock = QLabel("--:--:--")
        self._clock.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._clock.setStyleSheet(f"color:{COLOR_DIM};")
        lay.addWidget(self._clock)

        return w

    def _composer(self):
        wrap = QWidget()
        wrap.setFixedHeight(98)
        wrap.setStyleSheet(f"background:{COLOR_BG}; border-top:1px solid {COLOR_BORDER};")
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        upload = QPushButton("📎")
        upload.setFixedSize(46, 46)
        upload.setToolTip("Upload file")
        upload.clicked.connect(self._browse_file)
        upload.setStyleSheet(self._round_button(COLOR_PANEL, COLOR_TEXT))
        lay.addWidget(upload)

        self._mute_btn = QPushButton("🎙")
        self._mute_btn.setFixedSize(46, 46)
        self._mute_btn.setToolTip("Toggle microphone")
        self._mute_btn.clicked.connect(self._toggle_mute)
        self._mute_btn.setStyleSheet(self._round_button("#06351f", COLOR_GREEN))
        lay.addWidget(self._mute_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText(f"Message {ASSISTANT_NAME}...")
        self._input.setFixedHeight(48)
        self._input.setFont(QFont("Segoe UI", 11))
        self._input.returnPressed.connect(self._send)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background:{COLOR_PANEL};
                color:{COLOR_TEXT};
                border:1px solid {COLOR_BORDER};
                border-radius:20px;
                padding:0 16px;
            }}
            QLineEdit:focus {{ border:1px solid {COLOR_ACCENT}; }}
        """)
        lay.addWidget(self._input, stretch=1)

        send = QPushButton("➤")
        send.setFixedSize(48, 48)
        send.clicked.connect(self._send)
        send.setStyleSheet(self._round_button(COLOR_ACCENT, "#001018"))
        lay.addWidget(send)

        return wrap

    def _round_button(self, bg, fg):
        return f"""
            QPushButton {{
                background:{bg};
                color:{fg};
                border:1px solid {COLOR_BORDER};
                border-radius:23px;
                font-size:18px;
            }}
            QPushButton:hover {{
                border:1px solid {COLOR_ACCENT};
            }}
        """

    def _tick_clock(self):
        self._clock.setText(time.strftime("%H:%M:%S"))

    def _toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def _send(self):
        txt = self._input.text().strip()
        if not txt:
            return
        self._input.clear()
        self.chat.add_message(txt, "user")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(txt,), daemon=True).start()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Upload file to {ASSISTANT_NAME}", str(Path.home()), "All Files (*.*)")
        if path:
            self._on_file_selected(path)

    def _on_file_selected(self, path: str):
        self._current_file = path
        p = Path(path)
        size = self._fmt_size(p.stat().st_size)
        self._file_label.setText(f"Uploaded\n{p.name}\n{size}")
        self.chat.add_message(f"Uploaded file: {p.name}", "user")
        self.chat.add_message(f"I can see {p.name}. What would you like me to do with it?", "ai")
        if self.on_text_command:
            msg = (
                f"[FILE_UPLOADED] path={path} | name={p.name} | "
                f"type={p.suffix.lstrip('.')} | size={size} | "
                f"Briefly tell the user you can see the file '{p.name}' "
                f"({size}) has been uploaded and ask what they'd like to do with it."
            )
            threading.Thread(target=self.on_text_command, args=(msg,), daemon=True).start()

    def _fmt_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 ** 2:
            return f"{size/1024:.1f} KB"
        if size < 1024 ** 3:
            return f"{size/1024**2:.1f} MB"
        return f"{size/1024**3:.1f} GB"

    def _toggle_mute(self):
        self._muted = not self._muted
        if self._muted:
            self._mute_btn.setText("🔇")
            self._mute_btn.setStyleSheet(self._round_button("#3a0b16", COLOR_RED))
            self._apply_state("MUTED")
            self.chat.add_message("Microphone muted.", "ai")
        else:
            self._mute_btn.setText("🎙")
            self._mute_btn.setStyleSheet(self._round_button("#06351f", COLOR_GREEN))
            self._apply_state("LISTENING")
            self.chat.add_message("Microphone active.", "ai")

    def _apply_state(self, state: str):
        color = COLOR_GREEN
        if state == "SPEAKING":
            color = COLOR_ACCENT
        elif state == "THINKING":
            color = "#f59e0b"
        elif state == "MUTED":
            color = COLOR_RED

        self._status_card.setText(f"● {state}")
        self._status_card.setStyleSheet(f"""
            QLabel {{
                color:{color};
                background:{COLOR_PANEL};
                border:1px solid {COLOR_BORDER};
                border-radius:14px;
                padding:14px;
            }}
        """)

    def _receive_log(self, text: str):
        lower = text.lower()
        if lower.startswith("you:"):
            self.chat.add_message(text[4:].strip(), "user")
        elif lower.startswith("[nik]:"):
            self.chat.add_message(text[7:].strip(), "ai")
        elif lower.startswith(f"{ASSISTANT_NAME.lower()}:"):
            self.chat.add_message(text.split(":", 1)[1].strip(), "ai")
        else:
            self.chat.add_message(text.strip(), "ai")

    def _check_config(self) -> bool:
        if not API_FILE.exists():
            return False
        try:
            d = json.loads(API_FILE.read_text(encoding="utf-8"))
            return bool(d.get("gemini_api_key")) and bool(d.get("openrouter_api_key")) and bool(d.get("os_system"))
        except Exception:
            return False

    def _show_setup(self):
        self._overlay = SetupOverlay(self.centralWidget())
        self.resizeEvent(None)
        self._overlay.done.connect(self._on_setup_done)
        self._overlay.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_overlay") and self._overlay and self._overlay.isVisible():
            cw = self.centralWidget()
            self._overlay.setGeometry((cw.width() - 430) // 2, (cw.height() - 280) // 2, 430, 280)

    def _on_setup_done(self, key: str, or_key: str, os_name: str):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        API_FILE.write_text(json.dumps({
            "gemini_api_key": key,
            "openrouter_api_key": or_key,
            "os_system": os_name,
        }, indent=4), encoding="utf-8")

        self._ready = True
        if self._overlay:
            self._overlay.hide()
            self._overlay = None

        self._apply_state("LISTENING")
        self.chat.add_message(f"Setup complete. {ASSISTANT_NAME} is online.", "ai")


class _RootShim:
    def __init__(self, app: QApplication):
        self._app = app

    def mainloop(self):
        self._app.exec()

    def protocol(self, *_):
        pass


class JarvisUI:
    def __init__(self, face_path: str = "", size=None):
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._app.setStyle("Fusion")
        self._win = MainWindow(face_path)
        self._win.show()
        self.root = _RootShim(self._app)

    @property
    def muted(self) -> bool:
        return self._win._muted

    @muted.setter
    def muted(self, v: bool):
        if v != self._win._muted:
            self._win._toggle_mute()

    @property
    def current_file(self) -> str | None:
        return self._win._current_file

    @property
    def on_text_command(self):
        return self._win.on_text_command

    @on_text_command.setter
    def on_text_command(self, cb):
        self._win.on_text_command = cb

    def set_state(self, state: str):
        self._win._state_sig.emit(state)

    def write_log(self, text: str):
        self._win._log_sig.emit(text)

    def wait_for_api_key(self):
        while not self._win._ready:
            time.sleep(0.1)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")
