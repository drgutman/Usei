from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QApplication
from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import QTimer, Qt

from core.utils import SettingsManager
from core.signals import global_signals

settings_manager = SettingsManager()

class ConsoleWindow(QWidget):
    def __init__(self, parent=None, splash=None):
        super().__init__(parent)
        self.spinner_active = False
        self.spinner_frames = ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱",
                             "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]
        self.spinner_index = 0

        self.spinner_timer = QTimer()
        self.spinner_timer.setInterval(110)
        self.spinner_timer.timeout.connect(self.update_spinner)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont("Consolas", 11)
        self.console_text.setFont(font)
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 40, 0, 0.2);
                color: rgba(40, 125, 40, 1);
            }
        """)

        layout.addWidget(self.console_text)
        self.setLayout(layout)

        try:
            global_signals.output_signal.disconnect(self.update_console)
        except TypeError:
            pass

        global_signals.output_signal.connect(self.update_console)
        global_signals.startAnimationSignal.connect(self.start_spinner)
        global_signals.stopAnimationSignal.connect(self.stop_spinner)
        self.console_text.selectionChanged.connect(self.copy_selected_text)

    def copy_selected_text(self):
        selected_text = self.console_text.textCursor().selectedText()
        if selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
            
    def update_console(self, text):
        # Get the current text without the spinner line
        current_text = self.console_text.toPlainText()
        if self.spinner_active and current_text.strip().endswith(tuple(self.spinner_frames)):
            current_text = current_text.rsplit('\n', 1)[0]

        # Add the new text
        new_text = current_text
        if new_text and not new_text.endswith('\n'):
            new_text += '\n'
        new_text += text
        # if not new_text.endswith('\n'):
        #     new_text += '\n'

        # Update the text and add spinner if active
        self.console_text.setText(new_text)
        global_signals.statusbar_signal.emit(new_text)

        if self.spinner_active:
            cursor = self.console_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.console_text.append(self.spinner_frames[self.spinner_index])

        # Move cursor to end
        cursor = self.console_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_text.setTextCursor(cursor)
        QApplication.processEvents()

    def update_spinner(self):
        if not self.spinner_active:
            return

        # Get text without current spinner
        current_text = self.console_text.toPlainText()
        if current_text.strip().endswith(tuple(self.spinner_frames)):
            base_text = current_text.rsplit('\n', 1)[0] + '\n'
        else:
            base_text = current_text
            if not base_text.endswith('\n'):
                base_text += '\n'

        # Advance to next frame
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
        
        # Update text with new spinner frame
        self.console_text.setText(base_text + self.spinner_frames[self.spinner_index])

        # Keep cursor at end
        cursor = self.console_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console_text.setTextCursor(cursor)

    def start_spinner(self):
        if not self.spinner_active:
            self.spinner_active = True
            self.spinner_index = 0
            current_text = self.console_text.toPlainText()
            if not current_text.endswith('\n'):
                current_text += '\n'
            self.console_text.setText(current_text + self.spinner_frames[self.spinner_index])
            self.spinner_timer.start()

    def stop_spinner(self):
        if self.spinner_active:
            self.spinner_active = False
            self.spinner_timer.stop()
            
            # Remove spinner line
            current_text = self.console_text.toPlainText()
            if current_text.strip().endswith(tuple(self.spinner_frames)):
                current_text = current_text.rsplit('\n', 1)[0] + '\n'
                self.console_text.setText(current_text)