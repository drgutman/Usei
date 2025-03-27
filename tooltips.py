'''
CustomToolTip Class

    A custom tooltip class for PyQt6 applications, which allows for more flexible and dynamic tooltips.

Usage:
    1. Create an instance of CustomToolTip in your main window class.
    2. Install an event filter in your main window class to handle events using CustomToolTip.
    3. Set a custom property "custom_tooltip_text" on any widget to specify the tooltip text for that widget.

Example:

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            
            self.custom_tooltip = CustomToolTip()
            QCoreApplication.instance().installEventFilter(self)

        def eventFilter(self, obj, event):
            self.custom_tooltip.handle_event(obj, event)
            return super().eventFilter(obj, event)


To set a tooltip text on a widget:

    button = QtWidgets.QPushButton("Button 1")
    button.setProperty("custom_tooltip_text", "This is the tooltip text for button 1")

'''

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QGuiApplication

class ToolTips(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.label = QtWidgets.QLabel(self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.label.setStyleSheet("QLabel { padding-left: 3; padding-right: 3; padding-top: 1; padding-bottom: 1; margin: 0; border: 1px solid rgba(152, 152, 152, 0.5);}")

        self.show_tooltip_timer = QtCore.QTimer(self)
        self.show_tooltip_timer.timeout.connect(self.show_tooltip)
        self.show_tooltip_timer.setSingleShot(True)
        
        self.current_widget = None

    def set_text(self, text):
        self.label.setText(text)

    def show_tooltip(self):
        if self.current_widget:
            self.show()


    def handle_event(self, obj, event):
        screen = QGuiApplication.screenAt(QtGui.QCursor.pos())
        if not screen:
            return

        screen_rect = screen.availableGeometry()
        cursor_pos = QtGui.QCursor.pos()
        tooltip_size = self.sizeHint()

        if event.type() == QtCore.QEvent.Type.Enter:
            self.hide()

            # Calculate new position for Enter event
            x = min(cursor_pos.x() + 14, screen_rect.right() - tooltip_size.width())
            y = min(cursor_pos.y() + 14, screen_rect.bottom() - tooltip_size.height())
            self.move(x, y)

            self.set_text(obj.property("tooltip") or "")
            self.show_tooltip_timer.start(100)
            self.current_widget = obj

        elif event.type() == QtCore.QEvent.Type.Leave:
            if obj == self.current_widget:
                self.show_tooltip_timer.stop()
                self.hide()
                self.current_widget = None

        elif event.type() == QtCore.QEvent.Type.HoverMove:
            if obj == self.current_widget:
                # Calculate new position for HoverMove event
                x = min(cursor_pos.x() + 14, screen_rect.right() - tooltip_size.width())
                y = min(cursor_pos.y() + 14, screen_rect.bottom() - tooltip_size.height())
                self.move(x, y)
