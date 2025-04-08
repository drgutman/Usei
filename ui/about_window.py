from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QSize, QEvent, QUrl
from PyQt6.QtGui import QMovie, QImageReader, QDesktopServices, QIcon, QPixmap
# This line was replaced by the insert_content operation above

import sys
import os

from core.utils import position_window, SettingsManager
from ui.tooltips import ToolTips


settings_manager = SettingsManager()

class AboutWindow(QWidget):



    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        res_folder = os.path.join(base_dir, '_internal', 'ui', 'res')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        res_folder = os.path.join(base_dir, 'res')

    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        # Use Popup flag to auto-close on outside clicks
        self.setWindowFlags(Qt.WindowType.Popup)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.custom_tooltip = ToolTips()
        
        # Get GIF dimensions for the first animation
        reader = QImageReader(f"{self.res_folder}/banner.gif")
        gif_size = reader.size()
        if not gif_size.isValid():
            gif_size = QSize(100, 100)  # Fallback size

        # Configure GIF label for the first animation
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(gif_size)

        # Set up QMovie animation for the first animation
        self.movie = QMovie(f"{self.res_folder}/banner.gif")
        self.image_label.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.image_label)

        # Create a horizontal layout for the text and the second animation
        bottom_layout = QHBoxLayout()

        # Add the text label
        text = (
            "\n"
            "   USEI v 1.1.0 \n"
            "   有声 \n"
            "   adjective - voiced\n\n"
                   "     Usei is a text-to-speech (TTS) application that allows you \n"
            "   to convert text to speech using different voices and languages,\n"
            "   powered by the Kokoro TTS engine (onnx version).\n"
            "   created by @drgutman \n"
            "\n"
        )
        text_label = QLabel(text, self)
        text_label.setWordWrap(True)
        bottom_layout.addWidget(text_label)

        # Get GIF dimensions for the second animation
        reader_pizza = QImageReader(f"{self.res_folder}/pizza.gif")
        pizza_size = reader_pizza.size()
        if not pizza_size.isValid():
            pizza_size = QSize(100, 100)  # Fallback size

        # Configure GIF label for the second animation
        self.pizza_label = QLabel(self)
        self.pizza_label.setFixedSize(pizza_size)
        self.pizza_label.setCursor(Qt.CursorShape.PointingHandCursor)  # Show hand cursor

        # Create container widget
        pizza_container = QWidget()
        pizza_container_layout = QVBoxLayout(pizza_container)
        pizza_container_layout.setContentsMargins(0, 4, 0, 0)
        pizza_container_layout.setSpacing(2)
        pizza_container.setProperty("tooltip", "If you enjoy using this program, \n"
        "please help me to continue developing it by donating some money. \n"
        "I believe in open source but it already took me a lot of time \n"
        "to get it working properly and it will take a lot more to add new features. \n"
        "Hint: You can edit the amount by changing the number at the end of the URL ;)")
        pizza_container.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Add clickable pizza GIF
        pizza_container_layout.addWidget(self.pizza_label, 0, Qt.AlignmentFlag.AlignHCenter)

        # Add text under pizza
        self.pizza_text = QLabel(
            "Please donate \n a slice of pizza!\n", self
        )
        self.pizza_text.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                font-style: italic;
            }
        """)
        self.pizza_text.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.pizza_text.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pizza_text.installEventFilter(self) 
        pizza_container_layout.addWidget(self.pizza_text)

        # Set up movie
        self.pizza_movie = QMovie(f"{self.res_folder}/pizza.gif")
        self.pizza_label.setMovie(self.pizza_movie)
        self.pizza_movie.start()

        # Make clickable using event filter
        self.pizza_label.installEventFilter(self) 

        # Add container to layout
        bottom_layout.addWidget(pizza_container, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)        
        layout.addLayout(bottom_layout)

        # --- Contact Section ---
        contact_layout = QVBoxLayout()
        contact_layout.setContentsMargins(10, 10, 10, 10) # Add some padding
        contact_layout.setSpacing(5)

        contact_title = QLabel("Contact:")
        contact_title.setStyleSheet("font-weight: bold;")
        contact_layout.addWidget(contact_title)

        # Get theme for icons
        theme = settings_manager.get('SETTINGS/Theme', 'light').lower() # Default to light theme if not set
        icon_size = QSize(16, 16) # Standard icon size

        # GitHub Row
        github_layout = QHBoxLayout()
        github_icon_label = QLabel()
        github_icon_label.setStyleSheet("margin-left: 6px;")
        github_icon_path = os.path.join(self.res_folder, theme, 'github.ico')
        if os.path.exists(github_icon_path):
            github_icon = QIcon(github_icon_path)
            github_icon_label.setPixmap(github_icon.pixmap(icon_size))
        github_layout.addWidget(github_icon_label)

        github_text_label = QLabel('Github: <a href="https://github.com/drgutman/Usei">https://github.com/drgutman/Usei</a>')
        github_text_label.setOpenExternalLinks(True)
        github_layout.addWidget(github_text_label)
        github_layout.addStretch() # Push elements to the left
        contact_layout.addLayout(github_layout)

        # Discord Row
        discord_layout = QHBoxLayout()
        discord_icon_label = QLabel()
        discord_icon_label.setStyleSheet("margin-left: 6px;")
        discord_icon_path = os.path.join(self.res_folder, theme, 'discord.ico')
        if os.path.exists(discord_icon_path):
            discord_icon = QIcon(discord_icon_path)
            discord_icon_label.setPixmap(discord_icon.pixmap(icon_size))
        discord_layout.addWidget(discord_icon_label)

        discord_text_label = QLabel('Discord: <a href="https://discord.gg/x4s4Wznt">https://discord.gg/x4s4Wznt</a>')
        discord_text_label.setOpenExternalLinks(True)
        discord_layout.addWidget(discord_text_label)
        discord_layout.addStretch() # Push elements to the left
        contact_layout.addLayout(discord_layout)

        # Add contact section to main layout
        layout.addLayout(contact_layout)
        # --- End Contact Section ---

        self.setLayout(layout)
        position_window(self, position="center")


        # Ensure the popup has focus initially
        self.setFocus()

    def closeEvent(self, event):
        # Stop animation when closing the window
        self.movie.stop()
        self.pizza_movie.stop()
        super().closeEvent(event)

    def eventFilter(self, source, event):

        # Handle pizza GIF and text clicks without subclassing
        if (source in [self.pizza_label, self.pizza_text] and
            event.type() == QEvent.Type.MouseButtonPress):
            QDesktopServices.openUrl(QUrl("http://paypal.me/drgutman/20"))
            return True  # Event handled
        return super().eventFilter(source, event)
    
