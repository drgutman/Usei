from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QFrame, QMessageBox
from PyQt6.QtGui import QIcon, QFontDatabase

import sys
import os

from core.utils import SettingsManager
from core.theme import apply_theme, get_os_theme
from core.signals import global_signals

settings_manager = SettingsManager()

class CustomDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.initUI()
        self.programmatic_close = False

    def initUI(self):
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(f"ui/res/{get_os_theme()}/settings.ico"))
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        center_point = self.main_window.frameGeometry().center()
        settings_window_rect = self.frameGeometry()
        settings_window_rect.moveCenter(center_point)
        self.move(settings_window_rect.topLeft())

        program_layout = QVBoxLayout()
        program_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        border_frame = QFrame()
        border_frame.setFrameShape(QFrame.Shape.StyledPanel)
        border_frame.setFrameShadow(QFrame.Shadow.Raised)
        border_frame.setLayout(program_layout)

#### Program Settings ####

        program_settings_label = QLabel("Program settings:")
        program_layout.addWidget(program_settings_label)

        self.remember_check = QCheckBox("Remember program settings between sessions")
        program_layout.addWidget(self.remember_check)


        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setFixedWidth(60)
        theme_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.theme_dropdown = QComboBox()
        self.theme_dropdown.setMinimumWidth(90)
        self.theme_dropdown.addItems(['Light', 'Dark'])
        self.theme_dropdown.currentTextChanged.connect(lambda: apply_theme(self.theme_dropdown.currentText(), window=self.main_window))

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_dropdown)
        theme_layout.addStretch(1)
        program_layout.addLayout(theme_layout)



        scale_row_layout = QHBoxLayout()
        scale_label = QLabel("UI scale:")
        scale_label.setFixedWidth(60)
        scale_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.scale_spinbox = QDoubleSpinBox()
        self.scale_spinbox.setMinimumWidth(50)
        self.scale_spinbox.setValue(1.0)
        self.scale_spinbox.setMinimum(0.5)
        self.scale_spinbox.setMaximum(2.0)
        self.scale_spinbox.setSingleStep(0.1)
        scale_restart_label = QLabel("(requires restart)")

        scale_row_layout.addWidget(scale_label)
        scale_row_layout.addWidget(self.scale_spinbox)
        scale_row_layout.addWidget(scale_restart_label)
        scale_row_layout.addStretch(1)
        program_layout.addLayout(scale_row_layout) 

        self.confirmexit_check = QCheckBox("Confirm exit")
        program_layout.addWidget(self.confirmexit_check)

        self.show_console_check = QCheckBox("Show console")
        program_layout.addWidget(self.show_console_check)

        reset_settings_layout = QHBoxLayout()
        reset_settings_button = QPushButton("Reset")
        reset_settings_button.setFixedWidth(80)
        reset_settings_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        reset_settings_button.clicked.connect(self.reset_settings)
        reset_settings_layout.addWidget(reset_settings_button)

        reset_settings_label = QLabel("Resets the program settings to default")
        reset_settings_layout.addWidget(reset_settings_label)
        reset_settings_layout.setContentsMargins(0, 4, 0, 8)
        reset_settings_layout.addStretch(1)

        program_layout.addLayout(reset_settings_layout)


        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(0)
        divider.setLineWidth(0)
        divider.setStyleSheet("border: none;")
        program_layout.addWidget(divider)

#### Text Editor ####

        editor_settings_label = QLabel("Text editor settings:")
        program_layout.addWidget(editor_settings_label)

        font_frame = QFrame()
        font_frame.setFrameShape(QFrame.Shape.NoFrame)
        font_frame.setFrameShadow(QFrame.Shadow.Plain)
        font_frame.setStyleSheet("QFrame { border: none; } QLabel { border: none; }")

        font_layout = QVBoxLayout()
        font_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        font_row_layout = QHBoxLayout()
        font_label = QLabel("Font: ")
        font_label.setFixedWidth(52)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.font_dropdown = QComboBox()
        self.font_dropdown.setFixedWidth(180)
        available_fonts = QFontDatabase.families()
        self.font_dropdown.addItems(available_fonts)
        self.font_dropdown.currentIndexChanged.connect(self.changeFontFamily)
        font_row_layout.addWidget(font_label)
        font_row_layout.addWidget(self.font_dropdown)
        font_row_layout.addStretch(1)

        size_row_layout = QHBoxLayout()
        size_label = QLabel("Size: ")
        size_label.setFixedWidth(52)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setMinimumWidth(50)
        self.size_spinbox.setValue(0)
        self.size_spinbox.setMinimum(8)
        self.size_spinbox.setMaximum(72)
        current_font_size = self.main_window.tts_editor.font().pointSize()
        self.size_spinbox.setValue(current_font_size)
        self.previous_font_size = current_font_size


        self.size_spinbox.valueChanged.connect(self.settingsChangeFontSize)

        size_row_layout.addWidget(size_label)
        size_row_layout.addWidget(self.size_spinbox)
        size_row_layout.addStretch(1)

        font_layout.addLayout(font_row_layout)
        font_layout.addLayout(size_row_layout)

        font_frame.setLayout(font_layout)
        program_layout.addWidget(font_frame)

        layout.addWidget(border_frame)

        self.confirmTextModified_check = QCheckBox("Ask to save text on exit if it has been modified")
        program_layout.addWidget(self.confirmTextModified_check)

#### BUTTONS ####

        save_button = QPushButton("Save")
        save_button.setAutoDefault(False)
        save_button.setFixedWidth(80)
        save_button.clicked.connect(self.save_settings)

        cancel_button = QPushButton("Cancel")
        cancel_button.setAutoDefault(False)
        cancel_button.setFixedWidth(80)
        cancel_button.clicked.connect(self.close_settings)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.load_settings()

    def changeFontFamily(self):
        selected_font_family = self.font_dropdown.currentText()
        self.main_window.tts_editor.editorSetFontFamily(selected_font_family)

    def reset_settings(self):
        question_box = QMessageBox(self)
        question_box.setWindowTitle("Reset settings")
        question_box.setText("This will reset all the settings to the defaults. Are you sure?")
        question_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        question_box.setStyleSheet("QPushButton { margin: 0px; }")
        result = question_box.exec()
        if result == QMessageBox.StandardButton.Yes:
            settings_manager.reset_to_defaults()
            settings_manager.set('SETTINGS/WindowGeometry', None)
            settings_manager.set('SETTINGS/WindowState', None)
            settings_manager.set('SETTINGS/ConsoleDockGeometry', None)
            settings_manager.set('SETTINGS/TTSDockGeometry', None)
            settings_manager.set('SETTINGS/TTSDockVisible', None)
            self.load_settings("reset")
            apply_theme(settings_manager.get("SETTINGS/Theme"),self)
            self.main_window.statusbar.showMessage("Settings have been reset")
            global_signals.output_signal.emit("*** Settings have been reset \n")
        else:
            return

    def load_settings(self, reset = None):
        remember_window_position = settings_manager.get('SETTINGS/SaveProgramSettings')
        self.remember_check.setChecked(remember_window_position.lower() == 'true')
        current_theme = settings_manager.get('SETTINGS/Theme')
        self.theme_dropdown.setCurrentText(current_theme)
        current_scale = settings_manager.get('SETTINGS/UIScale')
        self.scale_spinbox.setValue(float(current_scale))
        self.previous_scale_value = float(current_scale)
        remember_confirmexit = settings_manager.get('SETTINGS/ConfirmExit')
        self.confirmexit_check.setChecked(remember_confirmexit.lower() == 'true')
        remember_console_window = settings_manager.get('SETTINGS/ShowConsole')
        self.show_console_check.setChecked(remember_console_window.lower() == 'true')

        if reset:
            index = self.font_dropdown.findText(settings_manager.get('EDITOR/Font'), Qt.MatchFlag.MatchExactly)
            if index != -1:
                self.font_dropdown.setCurrentIndex(index)
            else:
                print(f"Font '{settings_manager.get('EDITOR/Font')}' not found in the available fonts.")

            saved_font_size = settings_manager.get('EDITOR/FontSize')
            self.size_spinbox.setValue(saved_font_size)
        else:
            current_font_family = self.main_window.tts_editor.getCurrentFontFamily()
            index = self.font_dropdown.findText(current_font_family, Qt.MatchFlag.MatchExactly)
            if index != -1:
                self.font_dropdown.setCurrentIndex(index)
            else:
                print(f"Font '{current_font_family}' not found in the available fonts.")

            current_font_size = self.main_window.tts_editor.font().pointSize()
            self.size_spinbox.setValue(current_font_size)
        
        remember_confirmTextModified = settings_manager.get('EDITOR/ConfirmTextModified')
        self.confirmTextModified_check.setChecked(remember_confirmTextModified.lower() == 'true')

            

    def save_settings(self):
        remember_window_position_value = self.remember_check.isChecked()
        remember_confirmexit = self.confirmexit_check.isChecked()
        new_show_console_value = self.show_console_check.isChecked()
        old_show_console_value = settings_manager.get('SETTINGS/ShowConsole', True)
        if isinstance(old_show_console_value, str):
            old_show_console_value = old_show_console_value.lower() == 'true'

        remember_confirmTextModified = self.confirmTextModified_check.isChecked()

        settings_manager.set('SETTINGS/SaveProgramSettings', remember_window_position_value)
        settings_manager.set('SETTINGS/Theme', self.theme_dropdown.currentText())
        
        current_scale_value = self.scale_spinbox.value()
        settings_manager.set('SETTINGS/UIScale', self.scale_spinbox.value())
        
        settings_manager.set('SETTINGS/ConfirmExit', remember_confirmexit)
        settings_manager.set('SETTINGS/ShowConsole', new_show_console_value)
        settings_manager.set('EDITOR/Font', self.font_dropdown.currentText())
        settings_manager.set('EDITOR/FontSize', self.size_spinbox.value())
        settings_manager.set('EDITOR/ConfirmTextModified', remember_confirmTextModified)

        if new_show_console_value != old_show_console_value:
            # Check if main_window exists and has the method
            if hasattr(self.main_window, 'update_console_visibility'):
                self.main_window.update_console_visibility()

        if current_scale_value != self.previous_scale_value:
            restart = QMessageBox.question(
                self,
                "Restart Required",
                "Changes to the UI scale require a restart to take effect. Restart now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if restart == QMessageBox.StandardButton.Yes:
                QProcess.startDetached(sys.executable, sys.argv)
                sys.exit(0)
            else:
                self.programmatic_close = True
                self.close()
        else:
            self.programmatic_close = True
            self.close()


    def close_settings(self):
        remember_window_position_value = settings_manager.get('SETTINGS/SaveProgramSettings', 'true')
        current_theme = settings_manager.get('SETTINGS/Theme')
        self.remember_check.setChecked(remember_window_position_value.lower() == 'true')
        self.theme_dropdown.setCurrentText(current_theme)
        self.settingsChangeFontSize(self.previous_font_size)
        apply_theme(current_theme, window=self.main_window)
        self.close()

    def closeEvent(self, event):
        if not self.programmatic_close:
            self.close_settings()
            event.accept()
        else:
            event.accept()

    def settingsChangeFontSize(self, value):
        self.main_window.tts_editor.setExactFontSize(value)

def open_settings_window(main_window):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    dialog = CustomDialog(main_window)
    main_window.settings_window = dialog
    dialog.exec()
