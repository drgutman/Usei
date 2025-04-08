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

     v 1.1.0

Usei is a text-to-speech (TTS) application that allows you to convert text to speech using different voices and languages.
It uses the Kokoro TTS engine (onnx version) to render the text.

    INSTALLATION: 

Fresh venv:
    python -m venv .venv
    pip install -r requirements.txt

Build (from the activated .venv):
    pyinstaller --clean usei.spec

    
Change log:

    v1.0.0
        First release

    v1.1.0
        Interface:
            Improved loading bar animation in splash screen (added background animation too). There's still a small inconsistency that makes it go to 100% and then back at 98% or something but I can't figure it out for the life of me.             
            There was a small window/widget flickering into existence for a millisecond before the user clicks for the first time on Replace button in the toolbar.
            Fixed the statusbar label not showing the text fully. 
            Added a new SizeGrip because the default one wasn't visible. It was there and it was working, but you couldn't see it.
                (yes, I had to make a custom drawn sizegrip with tilted gradients, it's ridiculous how many quirks you find once you start digging)
            Made the splashscreen log widget taller.

        Features/Bug fix:
            Added python check at runtime so it doesn't crash the system anymore.
            Use UV for package management.
            Reorganized the folder structure.
            Streamlined the code and added better error logging and reporting during startup.
            Moved fugashi from requirements.txt to the module_loader function.
            Included pyopenjtalk to the source code bundled_libs along with several dlls so the user doesn't have to install cmake or vs_BuildTools in order to run the program.
            Changed the debug switch in settings to "show console tab" and added a toolbar icon for show console.
                (there's still a small bug when you move the audio player from the bottom dock to the right bottom dock in which the height is wrong, but couldn't find a way to fix it no matter what I tried)
            Modified the package check to only delete and reinstall the missing packages or those with a wrong version.

            GPU support? no. Just NO! ... I bashed my head on this for 3 or 4 days and I couldn't make it work. It has something to do with onnxruntime versions and their compatibility with the python version and then you need vs code built tools, and so on, and so on, and it still crashes so I rather not. It's fast enough on cpu alone.

Next:

    (I don't know, I'm kind of tired of working on this and I have more important stuff to do, so I'm going to take a break. Maybe I'll come back to it in the future, or if people start using it and donate a bit) 

    Add tooltips for the tts_settings
    Add stop rendering button under the animation.
    Make sure that the user doesn't need to run as administrator in order for it to work.
    Add .pdf and .epub and .doc support.
    Add streaming support.
    Add podcast functionality.



"""




from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QApplication
import sys
import os
from core.utils import SettingsManager
from ui.usei import MainWindow
from ui.splash_window import SplashWindow

settings_manager = SettingsManager()

scale = settings_manager.get("SETTINGS/UIScale")

if scale:
    os.environ["QT_SCALE_FACTOR"] = str(scale)


def main():
    app = QApplication(sys.argv)
    w, h = 800, 600
    main_win = MainWindow(w, h)
    
    splash_window = None

    splash_window = SplashWindow()
    splash_window.show_splash_window()
    splash_window.splash_closed.connect(main_win.show)
   

    # main_win.show()  # Show the main window directly when the splash_window parts are commented out -- for testing purposes only

    exit_code = app.exec()
    
    # """ Clean up before exit """
    if splash_window and hasattr(splash_window, 'module_loader_thread') and splash_window.module_loader_thread:
        if splash_window.module_loader_thread.isRunning():
            splash_window.module_loader_thread.quit()
            splash_window.module_loader_thread.wait(1000)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()


