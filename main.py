"""

     ▄█═╗    ▄█═╗  ▄███████═╗  ▄███████═╗  ▄█═╗
    ███ ║   ███ ║ ███ ╔═════╝ ███ ╔═════╝ ███ ║
    ███ ║   ███ ║ ███ ║       ███ ║       ███ ║
    ███ ║   ███ ║ █████████═╗ ███████═╗   ███ ║
    ███ ║   ███ ║ ╚═════███ ║ ███ ╔═══╝   ███ ║
    ███ ║   ███ ║ ▄     ███ ║ ███ ║       ███ ║
    ███ ║   ███ ║ ██╗   ███ ║ ███ ║       ███ ║
    ▀█████████▀╔╝ ▀████████ ║ █████████═╗ ███ ║
      ╚════════╝   ╚════════╝ ╚═════════╝ ╚═══╝    有声 - adjective - voiced


     v 0.1

Usei is a text-to-speech (TTS) application that allows you to convert text to speech using different voices and languages.
It uses the Kokoro TTS engine (onnx version) to render the text.

"""

import os
import usei
from utils import SettingsManager

settings_manager = SettingsManager()

scale = settings_manager.get("SETTINGS/UIScale")

if scale:
    os.environ["QT_SCALE_FACTOR"] = str(scale)

from PyQt6.QtWidgets import QApplication
import sys
from splash_window import SplashWindow



def main():
    app = QApplication(sys.argv)
    w, h = 800, 600
    main_win = usei.MainWindow(w, h)
    
    splash_window = None

    splash_window = SplashWindow()
    splash_window.show_splash_window()
    splash_window.splash_closed.connect(main_win.show)
   

    # main_win.show()  # Show the main window directly when the splash_window parts are commented out -- for testing purposes only

    exit_code = app.exec()
    
    # Clean up before exit
    if splash_window and hasattr(splash_window, 'module_loader_thread') and splash_window.module_loader_thread:
        if splash_window.module_loader_thread.isRunning():
            splash_window.module_loader_thread.quit()
            splash_window.module_loader_thread.wait(1000)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()


