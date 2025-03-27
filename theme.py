from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QColor

import platform
import winreg
import qdarktheme
import subprocess

from search_dialog import SearchDialog
from utils import SettingsManager

settings_manager = SettingsManager()

def set_main_window(window):
    global main_window
    main_window = window




qss_light = """
    QCheckBox:hover {
            border: none !important;
        }
    QPushButton {
            border-color: rgba(125, 125, 125, 1); 
            background-color: rgba(125, 125, 125, 0.2);
            color: rgba(100, 100, 100, 1);
        }
"""

qss_dark = """
    QCheckBox:hover {
            border: none !important;
        }
    QPushButton {
            border-color: rgba(125, 125, 125, 1); 
            background-color: rgba(125, 125, 125, 0.2);
            color: rgba(200, 200, 200, 1);
        }
"""





def apply_theme(theme, window):
    app = QApplication.instance()

    if theme == "Light":
        qdarktheme.setup_theme(
            theme="light",
            corner_shape="sharp",
            custom_colors={"primary": "#b0a097"},
            additional_qss=qss_light,
            )
    elif theme == "Dark":
        qdarktheme.setup_theme(
            theme="dark",
            corner_shape="sharp",
            custom_colors={"primary": "#8c7f78"},
            additional_qss=qss_dark,
            )


    icon_folder = f"res/{theme.lower()}/"

    button_names = [
        "tb_bttn_new_file",
        "tb_bttn_open_file",
        "tb_bttn_save",
        "tb_bttn_save_as",
        "tb_bttn_undo",
        "tb_bttn_redo",
        "tb_bttn_select_all",
        "tb_bttn_copy",
        "tb_bttn_cut",
        "tb_bttn_paste",
        "tb_bttn_delete",
        "tb_bttn_find",
        "tb_bttn_replace",
        "tb_bttn_wrap",
        "tb_bttn_settings",
        "tb_bttn_reset",
        "tb_bttn_about",
        "tb_bttn_theme",
    ]

    # Set icons dynamically by using the same filenames in different theme folders
    for button_name in button_names:
        if hasattr(window, button_name):
            button = getattr(window, button_name)
            icon_path = f"{icon_folder}{button_name.split('_', 2)[2]}.ico"
            button.setIcon(QIcon(icon_path))

    # Update AudioPlayerWidget icons
    if hasattr(window, 'audio_player_widget'):
        audio_player = getattr(window, 'audio_player_widget')

        
        if hasattr(audio_player, 'play_button'):
            audio_player.play_button.setIcon(QIcon(f"{icon_folder}play.ico"))
        if hasattr(audio_player, 'stop_button'):
            audio_player.stop_button.setIcon(QIcon(f"{icon_folder}stop.ico"))
        if hasattr(audio_player, 'mute_button'):
            if audio_player.audio_output.isMuted():
                audio_player.mute_button.setIcon(QIcon(f"{icon_folder}mute.ico"))
            else:
                audio_player.mute_button.setIcon(QIcon(f"{icon_folder}vol_high.ico"))


        if theme == "Dark":
            audio_player.volume_slider.fill_color = QColor(255, 255, 255, 40)
            audio_player.volume_slider.background_color = QColor(255, 255, 255, 40)
            audio_player.volume_slider.handle_color = QColor(255, 255, 255, 80)
        else:
            audio_player.volume_slider.fill_color = QColor(0, 0, 0, 40)
            audio_player.volume_slider.background_color = QColor(0, 0, 0, 40)
            audio_player.volume_slider.handle_color = QColor(0, 0, 0, 80)


    user_text_color = "white" if theme == "Dark" else "black"
    reply_text_color = "white" if theme == "Dark" else "black"
    user_title_color = "rgb(200,200,200, 1)" if theme == "Dark" else "rgb(80,80,80, 1)"
    reply_title_color = "rgb(200,200,200, 1)" if theme == "Dark" else "rgb(80,80,80, 1)"

    def change_text_colors():
        javascript_code = f"""
        document.querySelectorAll('.user-text').forEach(function(el) {{
            el.style.color = '{user_text_color}';
        }});
        document.querySelectorAll('.user-title').forEach(function(el) {{
            el.style.color = '{user_title_color}';
        }});
        document.querySelectorAll('.reply-text').forEach(function(el) {{
            el.style.color = '{reply_text_color}';
        }});
        document.querySelectorAll('.reply-title').forEach(function(el) {{
            el.style.color = '{reply_title_color}';
        }});
        """
    QTimer.singleShot(0, change_text_colors)

    if SearchDialog._instance is not None:
        SearchDialog._instance.update_icons()


def get_os_theme():
    os_name = platform.system()

    if os_name == "Windows":
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "Light" if value == 1 else "Dark"
        except Exception as e:
            print(f"Error: {e}")
            return None

    elif os_name == "Darwin":  # macOS
        try:
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
            return "Dark" if result.stdout.strip() == "Dark" else "Light"
        except Exception as e:
            print(f"Error: {e}")
            return None

    elif os_name == "Linux":
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], capture_output=True, text=True)
            theme_name = result.stdout.strip().strip("'")
            return "Dark" if "dark" in theme_name.lower() else "Light"
        except Exception as e:
            print(f"Error: {e}")
            return None

    else:
        print("Unsupported OS")
        return None
