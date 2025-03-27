from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel # QPushButton
from PyQt6.QtCore import pyqtSignal, Qt, pyqtSlot, QMetaObject, QTimer, QSize
from PyQt6.QtGui import QTextCursor, QFont, QMovie, QImageReader, QIcon
from PyQt6.QtWidgets import QTextEdit
import time

from theme import get_os_theme
from utils import position_window, SettingsManager
from signals import global_signals
from module_loader import load_heavy_modules
from progress_bar import AnimatedProgressBar


settings_manager = SettingsManager()

class SplashWindow(QWidget):
    splash_closed = pyqtSignal()

    def __init__(self, parent=None):
        super(SplashWindow, self).__init__(parent)
        self.initialized = False
        self.module_loader_thread = None

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Loading ...")
        self.setWindowIcon(QIcon(f"res/{get_os_theme()}/usei.ico"))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        layout.setSpacing(0)

        # Get GIF dimensions
        reader = QImageReader("res/_usei.gif")
        gif_size = reader.size()
        if not gif_size.isValid():
            gif_size = QSize(100, 100)  # Fallback size

        # Configure GIF label
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(gif_size)

        # Set the width of the window to match the GIF width
        self.setFixedWidth(gif_size.width())

        # Set up QMovie animation
        self.movie = QMovie("res/_usei.gif")
        self.image_label.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.image_label)

        # Create progress_bar
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { margin: 0; padding: 0;}")

        # Create download_bar
        self.download_bar = QProgressBar()
        self.download_bar.setRange(0, 100)
        self.download_bar.setValue(0)
        self.download_bar.setFixedHeight(4)
        self.download_bar.setFormat("")
        self.download_bar.setStyleSheet("QProgressBar { margin: 0; padding: 0; border: none; }")

        debug_mode = settings_manager.get("SETTINGS/DebugMode")        

        self.loading_text = QTextEdit(self)
        self.loading_text.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont("Consolas", 11)
        self.loading_text.setFont(font)
        self.loading_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 40, 0, 0.2);
                color: rgba(40, 125, 40, 1);
            }
        """)
        if debug_mode == "true":
            self.loading_text.setFixedHeight(300)
        else:
            self.loading_text.setFixedHeight(24)
            self.loading_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


        self.loading_text.setReadOnly(True)
        self.loading_text.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.download_bar)
        layout.addWidget(self.loading_text)
        self.initialized = True

        self.splash_shown_time = None
        self.ready_received = False
        self.signals_connected = False

        self.setLayout(layout)
        position_window(self, position="center")
        self.loading_text.selectionChanged.connect(self.copy_selected_text)

    def copy_selected_text(self):
        selected_text = self.loading_text.textCursor().selectedText()
        if selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)

    @pyqtSlot(str)
    def updateMessage(self, message):
        self.update_splash(message)

    @pyqtSlot(int)
    def updateProgress(self, progress):
        self.update_progress(progress)

    def update_progress(self, progress):
        current_value = self.progress_bar.value()
        new_value = min(max(current_value + progress, 0), 100)
        self.progress_bar.setValueAnimated(new_value)

    @pyqtSlot(int)
    def updateDownload(self, position):
        self.update_download(position)

    def update_download(self, position):
        self.download_bar.setValue(position)

    def show_splash_window(self):
        if not self.initialized:
            self.init_widgets()

        self.connect_signals()
        self.splash_shown_time = time.time() * 1000
        self.module_loader_thread = load_heavy_modules(
            self.on_modules_loaded,
            message_callback_target = self,
            progress_callback_target = self,
            download_callback_target = self,
            downState_callback_target = self
        )
        global_signals.error_signal.connect(self.on_error, Qt.ConnectionType.QueuedConnection)
        self.show()
        QApplication.processEvents()

    def on_modules_loaded(self, kokoro_instance):
        global kokoro
        kokoro = kokoro_instance
        self.kokoro_loaded = True
        self.update_progress(100)
        self.progress_bar.setValueAnimated(100) # this doesn't work for some strange reason.
        self.message_callback(f"Kokoro initialized.")
        self.close_splash_window()

    def on_ready_signal(self):
        self.ready_received = True
        self.message_callback("Files ready.")
        self.progress_bar.setValueAnimated(100)

    def connect_signals(self):
        if not self.signals_connected:
            global_signals.loading_signal.connect(self.update_splash, Qt.ConnectionType.QueuedConnection)
            global_signals.files_ready.connect(self.on_ready_signal, Qt.ConnectionType.QueuedConnection)
            self.signals_connected = True

    def disconnect_signals(self):
        if self.signals_connected:
            try:
                global_signals.loading_signal.disconnect(self.update_splash)
                global_signals.files_ready.disconnect(self.on_ready_signal)
            except (TypeError, RuntimeError):
                pass
            self.signals_connected = False

    def update_splash(self, text):
        cursor = self.loading_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if self.loading_text.toPlainText() and not self.loading_text.toPlainText().endswith('\n'):
            cursor.insertText('\n')
        cursor.insertText(text)
        self.loading_text.setTextCursor(cursor)
        QApplication.processEvents()
        with open('startup.log', 'w') as log_file:
            log_file.write(text + '\n')

    def message_callback(self, message):
        self.update_splash(message)

    def progress_callback(self, progress):
        self.update_progress(progress)

    def download_callback(self, position):
        self.update_download(position)

    def on_error(self, error_msg):
        self.update_splash(f"Error: {error_msg}")
        self.ready_received = False

    def cancel_loading(self):
        self.package_checker.stop()
        self.module_loader.stop()


    def close_splash_window(self):

        if self.module_loader_thread is not None:
            if self.module_loader_thread.isRunning():
                self.module_loader_thread.quit()
            self.module_loader_thread = None

        if self.ready_received:
            self.disconnect_signals()
            self.splash_closed.emit()

            QMetaObject.invokeMethod(self, "close", Qt.ConnectionType.QueuedConnection)




    def closeEvent(self, event):
        if self.module_loader_thread and self.module_loader_thread.isRunning():
            self.module_loader_thread.quit()
            self.module_loader_thread.wait(1000)
        event.accept() 



    # # Don't you, forget about me
    # # Don't, don't, don't, don't
    # # Don't you, forget about me

    # def closeEvent(self, event):
    #     # if self.ready_received:
    #     #     event.accept()
    #     # else:
    #     #     event.ignore()
    #     QTimer.singleShot(1050, lambda: event.accept())

    #     # event.accept()
