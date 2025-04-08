# ui/error_dialog.py
import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QPushButton, QSizePolicy, QApplication, QStyle, QMessageBox, QWidget)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QTimer

# Assuming error_debug.log is in the app's root directory
LOADER_ERROR_LOG_FILE = "error_debug.log"

def get_last_error_details():
    """Reads the last error block from the error log file."""
    try:
        if not os.path.exists(LOADER_ERROR_LOG_FILE):
            return "Error log file not found."

        with open(LOADER_ERROR_LOG_FILE, "r", encoding='utf-8') as f:
            content = f.read().strip()
            # Errors are separated by "--- YYYY-MM-DD HH:MM:SS ---"
            # Find the last occurrence of the separator
            last_separator_index = content.rfind("--- ")
            if last_separator_index == -1:
                # Maybe only one error, return the whole content
                return content if content else "Error log is empty or format is unexpected."
            else:
                # Return the content after the last separator
                return content[last_separator_index:]
    except Exception as e:
        return f"Failed to read error log: {e}"

class StartupErrorDialog(QDialog):
    def __init__(self, error_summary, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Application Startup Error")
        # Optional: Set an icon for the dialog window itself
        # self.setWindowIcon(QIcon("path/to/your/error_icon.ico"))

        self.setModal(True)
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # Top section: Icon and Summary
        top_layout = QHBoxLayout()
        icon_label = QLabel()
        # Use standard critical icon
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical)
        icon_label.setPixmap(icon.pixmap(32, 32)) # Adjust size as needed
        top_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        summary_label = QLabel(f"<b>Fatal Error:</b><br>{error_summary}")
        summary_label.setWordWrap(True)
        top_layout.addWidget(summary_label, stretch=1)
        layout.addLayout(top_layout)

        # Details Section (collapsible)
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 5, 0, 0) # Add some space above

        details_label = QLabel("<b>Details:</b>")
        details_layout.addWidget(details_label)

        self.details_text_edit = QTextEdit()
        self.details_text_edit.setReadOnly(True)
        self.details_text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.details_text_edit.setFontFamily("Consolas") # Or another monospace font
        self.details_text_edit.setText(get_last_error_details())
        details_layout.addWidget(self.details_text_edit)

        layout.addWidget(self.details_widget)

        button_layout = QHBoxLayout()

        button_layout.addStretch() # Push OK button to the right

        ok_button = QPushButton("OK")
        ok_button.setDefault(True)
        ok_button.setFixedWidth(60)
        ok_button.clicked.connect(self.close_application)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.adjustSize()


    def close_application(self):
        QApplication.instance().quit()

    def closeEvent(self, event):
        """Ensure closing the dialog via 'X' also quits the app."""
        self.close_application()
        event.accept()

    def reject(self):
        """Called when Escape key is pressed or reject() is explicitly called."""
        self.close_application()
        # Call the base class reject AFTER ensuring the app quits,
        # although quit() might make this redundant.
        super().reject()