from PyQt6.QtCore import pyqtSignal, QSettings, Qt, QPoint #, QTimer
from PyQt6.QtGui import QColor, QPalette, QBrush, QPainter, QPen, QPolygon
from PyQt6.QtWidgets import QSlider, QWidget, QDockWidget, QLabel  #, QMainWindow, QApplication

import re

main_window = None


class SettingsManager:
    def __init__(self):

        self.settings = QSettings("@drgutman", "Usei")

        # Initialize settings with default values if they are not already set
        self.default_settings = {
            "SETTINGS/SaveProgramSettings": False,
            "SETTINGS/Theme": "Light",
            "SETTINGS/UIScale": 1,
            "SETTINGS/ConfirmExit": True,
            "SETTINGS/DebugMode": False,
            
            "EDITOR/Font": "Consolas",
            "EDITOR/FontSize": 12,
            "EDITOR/Wrapped": "false",
            "EDITOR/ConfirmTextModified": True,

            "TTS/Language": None,
            "TTS/Voice": None,
            "TTS/Blending": False,
            "TTS/BlendingVoice": None,
            "TTS/BlendingBalance": 50,
            "TTS/Speed": "1",
            "TTS/OutputFile": None,

            "PLAYER/AutoPlay": False,
            "PLAYER/Volume": 50,
        }

        self.initialize_default_settings()

    def initialize_default_settings(self):
        # Initialize settings with default values if they are not already set
        for key, value in self.default_settings.items():
            if self.settings.value(key) is None:
                self.settings.setValue(key, value)

    def get(self, key, default_value=None):
        # Get the value of the specified setting.
        return self.settings.value(key, default_value)

    def set(self, key, value):
        # Set the value of the specified setting.
        self.settings.setValue(key, value)

    def reset_to_defaults(self):
        # Reset all settings to their default values.
        for key, value in self.default_settings.items():
            self.settings.setValue(key, value)

    def clear_settings(self):
        # Completely clear all stored settings.
        self.settings.clear()
        self.settings.sync()  # Ensure the settings are written to disk

settings_manager = SettingsManager()

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super(OverlayWidget, self).__init__(parent)
        self.setPalette(QPalette(QColor(255, 255, 255, 0)))  # Transparent background
        self.setAutoFillBackground(True)

class CustomSlider(QSlider):
    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        # Set a fixed height for the slider to maintain proportions
        self.setFixedHeight(16)
        # Remove the default handle
        self.setStyleSheet("QSlider::handle { background: transparent; }")
        # Set up colors
        theme = settings_manager.get('SETTINGS/Theme')
        # print(f"theme {theme}")
        if theme == "Dark":
            self.fill_color = QColor(255, 255, 255, 40)
            self.background_color = QColor(255, 255, 255, 40)
            self.handle_color = QColor(255, 255, 255)
        else:
            self.fill_color = QColor(0, 0, 0, 50)
            self.background_color = QColor(0, 0, 0, 50)
            self.handle_color = QColor(0, 0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            value = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(round(value))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            value = self.minimum() + ((self.maximum() - self.minimum()) * event.position().x()) / self.width()
            self.setValue(round(value))
            event.accept()
        else:
            super().mouseMoveEvent(event)
        
    def paintEvent(self, event):
        # Create a painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the background (empty triangle)
        painter.setPen(QPen(self.background_color, 1))
        painter.setBrush(QBrush(self.background_color))
        background_polygon = QPolygon([
            QPoint(0, self.height()),            # Bottom left
            QPoint(self.width(), 0),             # Top right
            QPoint(self.width(), self.height())  # Bottom right
        ])
        painter.drawPolygon(background_polygon)
        
        # Calculate the fill position based on the slider value
        value_ratio = self.value() / self.maximum() if self.maximum() > 0 else 0
        fill_x = int(value_ratio * self.width())
        
        # Draw the filled triangle
        if value_ratio > 0:
            painter.setPen(QPen(self.fill_color, 1))
            painter.setBrush(QBrush(self.fill_color))
            fill_polygon = QPolygon([
                QPoint(0, self.height()),            # Bottom left
                QPoint(fill_x, int(self.height() - value_ratio * self.height())),  # Point on the diagonal
                QPoint(fill_x, self.height())        # Bottom point at current value
            ])
            painter.drawPolygon(fill_polygon)
        
        # Draw the handle position
        if value_ratio > 0:
            handle_x = fill_x
            handle_y = int(self.height() - value_ratio * self.height())
            
            painter.setPen(QPen(self.handle_color, 2))
            painter.drawLine(handle_x, handle_y, handle_x, self.height())
        
        painter.end()

"""
    This doesn't work, I'm not sure if it's because of this code 
    or because of how the statusbar handles it and I'm too tired to figure out anymore.
    I've already wasted a full day trying to get that label to work properly and, 
    unless I make the statusbar 22 pixels or some shit like that,
    it clips the g. I tried to remove all the borders and paddings and all the other shit around it, it didn't work.

"""
class VerticallyAdjustedLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.vertical_offset = -6  # Move text up by 2 pixels

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(0, self.vertical_offset)
        rect = self.rect()
        rect.translate(0, -self.vertical_offset)
        painter.setClipRect(rect)
        super().paintEvent(event)

"""
    The SingletonMeta metaclass is designed to enforce the singleton pattern. 
    This means that any class using SingletonMeta as its metaclass 
    will have only one instance throughout the application's lifecycle.   

    I don't remember where I used this and it's not used anymore but I kept it because "who knows"

"""
# class SingletonMeta(type):
#     _instances = {}
#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             instance = super().__call__(*args, **kwargs)
#             cls._instances[cls] = instance
#         return cls._instances[cls]


def set_main_window(window):
    global main_window
    main_window = window

class CustomDockWidget(QDockWidget):
    closed = pyqtSignal()
    shown = pyqtSignal()  # New signal for when the widget is shown

    def closeEvent(self, event):
        self.parent().save_tts_dock_state()
        super().closeEvent(event)
        self.closed.emit()

    def showEvent(self, event):
        super().showEvent(event)
        self.shown.emit()  # Emit the signal when the widget is shown



"""
    Position the window either based on provided parameters or saved positions.
    If both parameters are provided, 'position' takes precedence.

    :param window: The window to be positioned.
    :param reference_widget: The widget relative to which the window should be centered. Optional.
    :param position: Tuple (x, y) for positioning the window or "center" for centering it. Optional.
    :param saved_position: Tuple (x, y) of saved window position. Optional.
"""
def position_window(window: QWidget, reference_widget=None, position=None, saved_position=None):
    # from PyQt6.QtGui import QScreen  # Local import to avoid circular dependency
    from PyQt6.QtGui import QGuiApplication  # Local import for QScreen

    # Check if the window exists before proceeding
    if not window:
        return

    # Use 'position' parameter if provided
    if position:
        if position == "center":
            if reference_widget:
                window.move(reference_widget.frameGeometry().center() - window.rect().center())
            else:
                window.move(QGuiApplication.primaryScreen().availableGeometry().center() - window.rect().center())
        else:
            if position == "centered":
                x, y = "center", "center"
            else:
                x, y = position
                window.move(x, y)

    # Otherwise, use 'saved_position' if provided
    elif saved_position:
        x, y = saved_position
        window.move(x, y)


def format_size(size_bytes):
    if size_bytes <= 0:
        return "unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024


def split_text_into_chunks(text, max_length=481):
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding the sentence to the current chunk exceeds the max length
        if len(current_chunk) + len(sentence) + 1 > max_length:
            # If the sentence itself is longer than the max length
            if len(sentence) > max_length:
                # Split the sentence by commas
                parts = sentence.split(',')
                for part in parts:
                    if len(current_chunk) + len(part) + 1 > max_length:
                        # If the part itself is longer than the max length, split by words
                        words = part.split()
                        for word in words:
                            if len(current_chunk) + len(word) + 1 > max_length:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                current_chunk += ' ' + word if current_chunk else word
                    else:
                        current_chunk += ',' + part if current_chunk else part
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
        else:
            current_chunk += ' ' + sentence if current_chunk else sentence

    # Add the last chunk if there's any remaining text
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks