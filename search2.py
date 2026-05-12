import sys
import time
import io
import webbrowser
import numpy as np
import mss
import pyautogui
import cv2

from PIL import Image
import win32clipboard

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QComboBox
)

from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPen,
    QIcon,
    QPixmap
)

from PyQt5.QtCore import (
    Qt,
    QPoint,
    QRect,
    QSize
)


# -------- Clipboard --------
def copy_image_to_clipboard(img):
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


# -------- Overlay --------
class Overlay(QWidget):
    def __init__(self, target, mode, parent=None):
        super().__init__()

        self.start = QPoint()
        self.end = QPoint()
        self.points = []
        self.drawing = False

        self.target = target
        self.mode = mode
        self.parent = parent

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        self.showFullScreen()
        self.setAttribute(Qt.WA_TranslucentBackground)

    # -------- Paint --------
    def paintEvent(self, event):
        painter = QPainter(self)

        # Dark overlay
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawRect(self.rect())

        if self.mode == "Rectangle":
            if not self.start.isNull() and not self.end.isNull():
                rect = QRect(self.start, self.end)

                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.drawRect(rect)

                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(QPen(QColor(0, 255, 0), 2))
                painter.drawRect(rect)

        elif self.mode == "Pencil":
            if len(self.points) > 1:
                painter.setPen(QPen(QColor(0, 150, 255), 3))

                for i in range(len(self.points) - 1):
                    painter.drawLine(self.points[i], self.points[i + 1])

    # -------- Mouse --------
    def mousePressEvent(self, e):
        if self.mode == "Rectangle":
            self.start = e.pos()
            self.end = self.start

        else:
            self.drawing = True
            self.points = [e.pos()]

        self.update()

    def mouseMoveEvent(self, e):
        if self.mode == "Rectangle":
            self.end = e.pos()

        else:
            if self.drawing:
                self.points.append(e.pos())

        self.update()

    def mouseReleaseEvent(self, e):
        if self.mode == "Rectangle":
            self.end = e.pos()

        else:
            self.drawing = False
            self.points.append(e.pos())

        self.capture_and_search()

        self.start = QPoint()
        self.end = QPoint()
        self.points = []

        self.update()
        self.close()

        if self.parent:
            self.parent.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

            if self.parent:
                self.parent.show()

    # -------- Capture --------
    def capture_and_search(self):
        with mss.mss() as sct:
            screen = np.array(sct.grab(sct.monitors[1]))

        if self.mode == "Rectangle":
            x1 = min(self.start.x(), self.end.x())
            y1 = min(self.start.y(), self.end.y())
            x2 = max(self.start.x(), self.end.x())
            y2 = max(self.start.y(), self.end.y())

            if x2 - x1 < 5 or y2 - y1 < 5:
                return

            crop = screen[y1:y2, x1:x2]

        elif self.mode == "Pencil":
            if len(self.points) < 3:
                return

            pts = np.array(
                [[p.x(), p.y()] for p in self.points],
                dtype=np.int32
            )

            x, y, w, h = cv2.boundingRect(pts)
            crop = screen[y:y + h, x:x + w]

        img = Image.fromarray(crop)

        copy_image_to_clipboard(img)
        open_target(self.target)


# -------- Open Target --------
def open_target(target):

    if target == "Google":
        webbrowser.open("https://lens.google.com/")
        time.sleep(5)
        pyautogui.hotkey("ctrl", "v")

    elif target == "ChatGPT":
        webbrowser.open("https://chat.openai.com/")
        time.sleep(5)
        pyautogui.hotkey("ctrl", "v")

    elif target == "Copilot":
        webbrowser.open("https://copilot.microsoft.com/")
        time.sleep(5)
        pyautogui.hotkey("ctrl", "v")

    elif target == "Gemini":
        webbrowser.open("https://gemini.google.com/")
        time.sleep(5)
        pyautogui.hotkey("ctrl", "v")


# -------- Main App --------
class MainApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ai Search Tool")
        self.setWindowIcon(QIcon("logo.png"))
        self.setGeometry(300, 200, 350, 260)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint
        )

        layout = QVBoxLayout()

        # -------- App Logo --------
        logo = QLabel()
        pixmap = QPixmap("logo.png")
        logo.setPixmap(
            pixmap.scaled(
                80,
                80,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        logo.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo)

        # -------- Platform --------
        layout.addWidget(QLabel("SEARCH PLATFORM"))

        self.platform = QComboBox()

        self.platform.addItem(
            QIcon("google.png"),
            "Google"
        )

        self.platform.addItem(
            QIcon("chatgpt.png"),
            "ChatGPT"
        )

        self.platform.addItem(
            QIcon("copilot.png"),
            "Copilot"
        )

        self.platform.addItem(
            QIcon("gemini.png"),
            "Gemini"
        )

        self.platform.setIconSize(QSize(24, 24))

        self.platform.setStyleSheet("""
            QComboBox {
                padding: 8px;
                font-size: 14px;
            }

            QComboBox QAbstractItemView {
                selection-background-color: #444;
            }
        """)

        layout.addWidget(self.platform)

        # -------- Mode --------
        layout.addWidget(QLabel("MODE"))

        self.mode = QComboBox()

        self.mode.addItem(
            QIcon("rectangle.png"),
            "Rectangle"
        )

        self.mode.addItem(
            QIcon("pencil.png"),
            "Pencil"
        )

        self.mode.setIconSize(QSize(24, 24))

        layout.addWidget(self.mode)

        # -------- Start Button --------
        self.start_btn = QPushButton(
            QIcon("capture.png"),
            " Start Selection"
        )

        self.start_btn.setIconSize(QSize(24, 24))

        self.start_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
            }
        """)

        self.start_btn.clicked.connect(self.start_overlay)

        layout.addWidget(self.start_btn)

        # -------- Exit Button --------
        self.exit_btn = QPushButton(
            QIcon("exit.png"),
            " Exit"
        )

        self.exit_btn.setIconSize(QSize(24, 24))

        self.exit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 14px;
            }
        """)

        self.exit_btn.clicked.connect(self.close)

        layout.addWidget(self.exit_btn)

        self.setLayout(layout)

    # -------- Start Overlay --------
    def start_overlay(self):
        self.hide()

        self.overlay = Overlay(
            self.platform.currentText(),
            self.mode.currentText(),
            parent=self
        )

        self.overlay.show()


# -------- Run --------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainApp()
    window.show()

    sys.exit(app.exec_())
