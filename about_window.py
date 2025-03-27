from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QSize, QEvent, QUrl
from PyQt6.QtGui import QMovie, QImageReader, QDesktopServices


from utils import position_window
from tooltips import ToolTips


class AboutWindow(QWidget):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        # Use Popup flag to auto-close on outside clicks
        self.setWindowFlags(Qt.WindowType.Popup)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.custom_tooltip = ToolTips()
        
        # Get GIF dimensions for the first animation
        reader = QImageReader("res/_usei.gif")
        gif_size = reader.size()
        if not gif_size.isValid():
            gif_size = QSize(100, 100)  # Fallback size

        # Configure GIF label for the first animation
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(gif_size)

        # Set up QMovie animation for the first animation
        self.movie = QMovie("res/_usei.gif")
        self.image_label.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.image_label)

        # Create a horizontal layout for the text and the second animation
        bottom_layout = QHBoxLayout()

        # Add the text label
        text = (
            "\n"
            "   USEI v 0.1 beta \n"
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
        reader_pizza = QImageReader("res/pizza.gif")
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
        self.pizza_movie = QMovie("res/pizza.gif")
        self.pizza_label.setMovie(self.pizza_movie)
        self.pizza_movie.start()

        # Make clickable using event filter
        self.pizza_label.installEventFilter(self) 

        # Add container to layout
        bottom_layout.addWidget(pizza_container, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)        
        layout.addLayout(bottom_layout)
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
    
