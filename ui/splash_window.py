from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar, QLabel, QMessageBox, QTextEdit # QPushButton
from PyQt6.QtCore import pyqtSignal, Qt, pyqtSlot, QMetaObject, QTimer, QSize
from PyQt6.QtGui import QTextCursor, QFont, QMovie, QImageReader, QIcon

import time
import os
import sys

from core.theme import get_os_theme
from core.utils import position_window, SettingsManager
from core.signals import global_signals
from core.module_loader import load_heavy_modules
from ui.progress_bar import IndeterminateAnimatedProgressBar
from ui.error_dialog import StartupErrorDialog

settings_manager = SettingsManager()

class SplashWindow(QWidget):

    splash_closed = pyqtSignal()

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
        res_folder = os.path.join(base_dir, '_internal', 'ui', 'res')
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        res_folder = os.path.join(base_dir, 'res')


    def __init__(self, parent=None):
        super(SplashWindow, self).__init__(parent)
        self.initialized = False
        self.module_loader_thread = None
        self.loading_successful = False
        self.kokoro_instance = None
        self.startup_log_written = False

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Loading ...")
        self.setWindowIcon(QIcon(f"{self.res_folder}/usei.ico"))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        layout.setSpacing(0)

        # Get GIF dimensions
        reader = QImageReader(f"{self.res_folder}/banner.gif")
        gif_size = reader.size()
        if not gif_size.isValid():
            gif_size = QSize(100, 100)  # Fallback size

        # Configure GIF label
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(gif_size)

        # Set the width of the window to match the GIF width
        self.setFixedWidth(gif_size.width())

        # Set up QMovie animation
        self.movie = QMovie(f"{self.res_folder}/banner.gif")
        self.image_label.setMovie(self.movie)
        self.movie.start()

        layout.addWidget(self.image_label)

        # Create progress_bar
        self.progress_bar = IndeterminateAnimatedProgressBar()
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
        self.loading_text.setFixedHeight(120)

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
        self.progress_bar.set_background_animation_enabled

    def copy_selected_text(self):
        selected_text = self.loading_text.textCursor().selectedText()
        if selected_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)

    @pyqtSlot(str)
    def updateMessage(self, message):
        self.update_splash(message)

    @pyqtSlot(str)
    def on_loader_error(self, error_msg):
        """Handles errors explicitly emitted by the ModuleLoaderThread."""
        # Ensure loading is marked as failed
        self.loading_successful = False

        # Log the summary error to the splash screen's log area (optional)
        self.update_splash(f"ERROR DETECTED: {error_msg}")

        # Stop progress animation
        self.progress_bar._keep_alive_timer.stop()
        self.progress_bar.set_background_animation_enabled(False)
        self.movie.stop()

        # --- Show the Custom Error Dialog ---
        error_dialog = StartupErrorDialog(error_summary=error_msg, parent=self)
        error_dialog.exec() # Show the modal dialog


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
                # self.init_widgets() # This seems redundant if called in __init__
                pass # Assuming __init__ always runs

            self.connect_signals() # Connect global signals if needed
            self.splash_shown_time = time.time() * 1000
            self.loading_successful = False
            self.kokoro_instance = None
            self.module_loader_thread = load_heavy_modules(
                callback_function=self.on_modules_loaded,
                message_callback_target=self,
                progress_bar_widget=self.progress_bar,
                download_callback_target=self,
                downState_callback_target=self
            )


            self.module_loader_thread.set_next_progress_milestone.connect(
                self.progress_bar.set_next_milestone_target,
                Qt.ConnectionType.QueuedConnection
            )

            self.module_loader_thread.error.connect(self.on_loader_error)
            self.module_loader_thread.finished.connect(self.on_loader_finished)
            
            self.connect_signals() # Contains global_signals.files_ready connection
            self.module_loader_thread.start()
            self.show()
            QApplication.processEvents()

# THIS HANDLES THE THREAD FINISHING (FOR ANY REASON)
    @pyqtSlot()
    def on_loader_finished(self):
        """Called when the ModuleLoaderThread finishes execution (success, error, or other)."""
        self.update_splash("Loading process finished.")
        self.progress_bar._keep_alive_timer.stop()
        if not self.loading_successful:
            self.update_splash("Loading finished, but success signal was not received. Check logs for errors.")
            self.progress_bar.set_background_animation_enabled(False)
            # Keep splash open


    # THE ACTUAL CLOSING LOGIC (called by timer from on_modules_loaded)
    def close_splash_window_final(self):
        """The actual closing action, called after success."""
        if self.module_loader_thread is not None:
             # Optional: Wait briefly for thread to fully terminate if needed,
             # but it should be finished if on_modules_loaded was called.
             # self.module_loader_thread.wait(100)
             self.module_loader_thread = None

        self.progress_bar._keep_alive_timer.stop()
        self.progress_bar._bg_animation_timer.stop()

        self.disconnect_signals() # Disconnect global signals
        self.splash_closed.emit() # Signal that main window can open (pass self.kokoro_instance if needed)
        self.close() # Close the splash window widget


    def on_modules_loaded(self, kokoro_instance):
        """Called by the loader thread DIRECTLY upon successful instantiation."""
        self.loading_successful = True
        self.kokoro_instance = kokoro_instance # Store if main window needs it
        self.updateMessage(f"Core modules initialized successfully.")
        self.progress_bar.setValueAnimated(100.0) # Ensure progress hits 100 on success
        self.progress_bar.set_next_milestone_target(100)
        QTimer.singleShot(200, self.close_splash_window_final)
        

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

    def update_splash(self, text): # Receives potentially timestamped text
        cursor = self.loading_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if self.loading_text.toPlainText() and not self.loading_text.toPlainText().endswith('\n'):
            cursor.insertText('\n')
        cursor.insertText(text)
        self.loading_text.setTextCursor(cursor)
        self.loading_text.ensureCursorVisible()
        QApplication.processEvents()

        # Use the flag correctly for 'w' vs 'a' mode
        log_mode = 'w'
        # Check existence AND value of the flag
        if not hasattr(self, 'startup_log_written') or not self.startup_log_written:
             self.startup_log_written = True # Set flag AFTER first write

        try:
            with open('startup.log', log_mode, encoding='utf-8') as log_file:
                log_file.write(text + '\n')
        except Exception as e:
            print(f"Error writing to startup.log: {e}")


    def message_callback(self, message):
        self.update_splash(message)

    def progress_callback(self, progress):
        self.update_progress(progress)

    def download_callback(self, position):
        self.update_download(position)

    def on_error(self, error_msg):
        self.update_splash(f"Error: {error_msg}")
        self.ready_received = False



    def closeEvent(self, event):
        # Ensure timers are stopped if window is closed prematurely
        try:
            self.progress_bar._keep_alive_timer.stop()
            self.progress_bar._bg_animation_timer.stop()
        except AttributeError:
             pass # Ignore if progress_bar doesn't exist yet
        if self.module_loader_thread and self.module_loader_thread.isRunning():
            self.module_loader_thread._stop_requested = True # Signal thread to stop
            # self.module_loader_thread.quit() # Might be too abrupt
            self.module_loader_thread.wait(500) # Wait briefly
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
