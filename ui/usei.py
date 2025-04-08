from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QFrame, QSizePolicy, QMessageBox, QDockWidget, QTabWidget, QToolButton, QToolBar, QFileDialog, QLabel, QSizeGrip
from PyQt6.QtCore import Qt, QSize, QByteArray
from PyQt6.QtGui import QIcon 


from core.theme import apply_theme, get_os_theme
from core.utils import SettingsManager, set_main_window, position_window, CustomDockWidget
from ui.settings import open_settings_window
from core.signals import global_signals
from ui.splash_window import SplashWindow
from ui.about_window import AboutWindow
from ui.search_dialog import show_search_dialog
from ui.LineCountTextEdit import LineCountTextEdit
from ui.audio_player import AudioPlayerWidget
from ui.tts_settings import TTSPropertiesWindow
from ui.tooltips import ToolTips
from ui.console import ConsoleWindow

settings_manager = SettingsManager()

class MainWindow(QMainWindow):
    
    def __init__(self, w, h, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.custom_tooltip = ToolTips()
        self.splash = SplashWindow()

        QApplication.instance().installEventFilter(self)

        set_main_window(self)
        self.setWindowTitle("Usei")
        self.setWindowIcon(QIcon(f"ui/res/usei_filled.ico"))

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QToolBar(self)
        icon_size = QSize(20, 20)
        self.toolbar.setIconSize(icon_size)
        self.toolbar.setContentsMargins(2, 0, 0, 0)

        buttons = [
            ('new_file', 'ui/res/empty.ico', 'New File'),
            ('open_file', 'ui/res/empty.ico', 'Open File'),
            ('save', 'ui/res/empty.ico', 'Save'),
            ('save_as', 'ui/res/empty.ico', 'Save As'),
            ('undo', 'ui/res/empty.ico', 'Undo'),
            ('redo', 'ui/res/empty.ico', 'Redo'),
            ('select_all', 'ui/res/empty.ico', 'Select All'),
            ('copy', 'ui/res/empty.ico', 'Copy'),
            ('cut', 'ui/res/empty.ico', 'Cut'),
            ('paste', 'ui/res/empty.ico', 'Paste'),
            ('delete', 'ui/res/empty.ico', 'Delete'),
            ('find', 'ui/res/empty.ico', 'Find (Ctrl+F)'),
            ('replace', 'ui/res/empty.ico', 'Replace (Ctrl+Shift+F)'),
            ('wrap', 'ui/res/empty.ico', 'Word Wrap'),
            ('console', 'ui/res/empty.ico', 'Show Console'),
            ('settings', 'ui/res/empty.ico', 'Settings'),
            ('about', 'ui/res/empty.ico', 'About'),
            ("theme", "ui/res/empty.ico", "It's black, it's white. He!He!")
        ]

        for name, icon_path, tooltip in buttons:

            button = QToolButton(self)
            button.setIcon(QIcon(icon_path))
            button.setProperty("tooltip", tooltip)
            button.setObjectName(f"tb_bttn_{name}")

            if name == "undo":  #<<<<<< separator
                separator = QFrame(self)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                self.toolbar.addWidget(separator)

            if name == "select_all":  #<<<<<< separator
                separator = QFrame(self)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                self.toolbar.addWidget(separator)

            if name == "find":  #<<<<<< separator
                separator = QFrame(self)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                self.toolbar.addWidget(separator)

            if name == 'wrap':
                button.setCheckable(True)
                is_wrapped = settings_manager.get("EDITOR/Wrapped").lower() == "true"
                button.setChecked(is_wrapped)

            if name == "settings":  #<<<<<< separator
                separator = QFrame(self)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                self.toolbar.addWidget(separator)

            if name == 'console':
                button.setCheckable(True)
                is_visible = settings_manager.get("SETTINGS/ShowConsole").lower() == "true"
                button.setChecked(is_visible)

            if name == "about":  #<<<<<< separator
                separator = QFrame(self)
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                self.toolbar.addWidget(separator)

            if name == 'theme':  #<<<<<< spacer
                spacer = QWidget(self)
                spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                self.toolbar.addWidget(spacer)



            setattr(self, f"tb_bttn_{name}", button)

            button.clicked.connect(lambda checked, name=name: self.tb_click_function(name))

            self.toolbar.addWidget(button)

        layout.addWidget(self.toolbar)

        self.workspace = QFrame(self)
        self.workspace.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.workspace_layout = QVBoxLayout(self.workspace)
        self.workspace_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_layout.setSpacing(0)
        layout.addWidget(self.workspace)

        #### EDITOR ####

        self.tts_editor = LineCountTextEdit(self)
        self.tts_editor.setContentsMargins(0, 0, 0, 0)

        editor_font = settings_manager.get('EDITOR/Font')
        self.tts_editor.editorSetFontFamily(editor_font)
        editor_font_size = int(settings_manager.get('EDITOR/FontSize'))
        self.tts_editor.setExactFontSize(editor_font_size)
        self.workspace_layout.addWidget(self.tts_editor)
        self.tts_editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        
    #### CONSOLE DOCK ####

        debug_mode = settings_manager.get("SETTINGS/DebugMode")

        self.consoleDockWidget = QDockWidget('⸽⸽', self)
        self.consoleDockWidget.setObjectName("ConsoleDockWidget")
        self.consoleDockWidget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        self.audio_player_widget = AudioPlayerWidget()

        self.console_window = ConsoleWindow()
        self.output_tab = QWidget()
        self.output_tab_layout = QVBoxLayout(self.output_tab)
        self.output_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.output_tab_layout.addWidget(self.audio_player_widget)
        # Create the container widget for the "Log" tab
        self.log_tab = QWidget()
        self.log_tab_layout = QVBoxLayout(self.log_tab)
        self.log_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.log_tab_layout.addWidget(self.console_window)
        self.console_window.setStyleSheet("margin: 0; padding: 0;") # Apply style here

        self.console_tab_widget = QTabWidget(self.consoleDockWidget)
        self.console_tab_widget.setTabPosition(QTabWidget.TabPosition.South)
        self.console_tab_widget.setObjectName("ConsoleTabs") # Give it an object name for styling/debugging
            
        self.console_tab_widget.setStyleSheet("""
            QTabBar::tab {
                color: rgba(125, 125, 125, 0.5);
                background: rgba(125, 125, 125, 0.1);
                border-top: 1px; border-bottom: none; border-left: 1px; border-right: 1px;
                padding-top: 0px; padding-bottom: 2px; padding-left: 4px; padding-right: 4px;
            }
            QTabBar::tab:selected {
                color: rgba(125, 125, 125, 1);
                border-top: none;
                border-bottom: 2px solid rgba(125, 125, 125, 1);
                background: rgba(173, 173, 173, 0.3);
            }
        """)

            # self.log_tab = QWidget()
        self.console_tab_widget.addTab(self.output_tab, " Output ")
        self.consoleDockWidget.setWidget(self.console_tab_widget)


        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.consoleDockWidget)

        self.update_console_visibility()


    #### SETTINGS DOCK ####

        self.TTSDockWidget = CustomDockWidget('⸽⸽  TTS Settings', self)
        self.TTSDockWidget.setObjectName("TTSDockWidget")
        self.TTSDockWidget.setContentsMargins(0, 0, 0, 0)

        self.tts_properties_window = TTSPropertiesWindow(tts_editor=self.tts_editor, audio_player=self.audio_player_widget)
        self.tts_properties_window.setContentsMargins(0, 0, 0, 0)
        self.TTSDockWidget.setWidget(self.tts_properties_window)

        # Set allowed areas for the dock widget
        self.TTSDockWidget.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.TTSDockWidget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.TTSDockWidget)

    #### STATUSBAR ####

        self.setCentralWidget(container)

        self.statusbar = self.statusBar()
        # Keep a minimal height, maybe slightly more than font but not excessively large
        STATUS_BAR_MIN_HEIGHT = 20 # Adjust if needed (e.g., 18, 20, 22)
        self.statusbar.setMinimumHeight(STATUS_BAR_MIN_HEIGHT)
        self.update_statusbar("Ready")

        self.statusbar.setSizeGripEnabled(False)

        # Create the standard label
        self.statusbar_text_stats = QLabel(" ", self)
        # Keep VCenter - the margin will adjust the widget's position
        self.statusbar_text_stats.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.statusbar_text_stats.setObjectName("StatusBarTextStatsLabel")
        self.statusbar_text_stats.setMinimumHeight(18)
        # No minimum height on label itself for now

        # Add label
        self.statusbar.addPermanentWidget(self.statusbar_text_stats)

        # # Create and add size grip
        size_grip = QSizeGrip(self.statusbar)
        size_grip.setFixedSize(17, 16)
        size_grip.setObjectName("StatusBarSizeGrip")
        self.statusbar.addPermanentWidget(size_grip)


        theme = settings_manager.get('SETTINGS/Theme')
        # Determine the semi-transparent grip color based on theme
        grip_rgba_color = 'rgb(150, 150, 150)' if theme == 'Dark' else 'rgb(125, 125, 125)'

        # --- Apply Stylesheet ---
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                /* border: 1px solid blue; */ /* Debug: See label bounds */
                padding: 0px; /* Overall status bar padding */
                margin: 0px;
                min-height: {STATUS_BAR_MIN_HEIGHT}px;
                /* Ensure background matches theme if needed */
                /* background-color: #333; */ /* Example */
            }}
            QStatusBar::item {{
                border: 0px;  /* No border around the layout item */
                padding: 0px; /* Crucial: No padding *inside* the item's slot */
                margin: 0px;  /* Crucial: No margin *around* the item's slot */
            }}
            QLabel#StatusBarTextStatsLabel {{
                /* === Negative Top Margin === */
                margin-top: -2px; /* Pull the entire QLabel widget up by 2 pixels */
                margin-bottom: 2px; /* Add margin below to compensate for the pull-up */
                                    /* prevents bottom clipping / overlap issues */

                /* Label's internal padding for text spacing */
                padding-left: 3px;
                padding-right: 3px;
                padding-top: -1px;
                padding-bottom: 0px;

                /* border: 1px solid red; */ /* Debug: See label bounds */
            }}
            QLabel#StatusBarTextStatsLabel:hover {{
                background-color: transparent; /* Explicitly keep transparent on hover */
                /* Or set it to the exact background color of QStatusBar if transparency causes issues */
                /* background-color: #333; */ /* Example if status bar is #333 */
            }}

            QSizeGrip#StatusBarSizeGrip {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0      transparent, /* Start transparent */
                    stop:0.624  transparent, /* End transparency just before first line */
                    stop:0.625    {grip_rgba_color}, /* Start first line */
                    stop:0.668   {grip_rgba_color}, /* End first line */
                    stop:0.669  transparent, /* Start first gap */
                    stop:0.736  transparent, /* End first gap */
                    stop:0.737   {grip_rgba_color}, /* Start second line */
                    stop:0.832    {grip_rgba_color}, /* End second line */
                    stop:0.833  transparent, /* Start second gap */
                    stop:0.88  transparent, /* End second gap */
                    stop:0.881    {grip_rgba_color}, /* Start third line */
                    stop:1      {grip_rgba_color}  /* End third line (fills to the corner) */
                );
                width: 17px;
                height: 16px;
                border: none; /* Ensure no border interferes */
                /* Your positioning margins */
                margin-right: 2px;
                margin-bottom: 1px;
                padding: 0px; /* Just to be safe */
            }}

        """)

        # Connect signals
        global_signals.statusbar_signal.connect(self.update_statusbar)
        global_signals.text_stats_signal.connect(self.update_text_stats)

        self.statusbar.setVisible(True)

        self.resize(w, h)


        save_window_position = settings_manager.get('SETTINGS/SaveProgramSettings')
        saved_window_state = settings_manager.get('SETTINGS/WindowState')
        saved_window_geometry = settings_manager.get('SETTINGS/WindowGeometry')

        if saved_window_geometry == "Default":
            position_window(self, position="center")

        if save_window_position:
            if saved_window_geometry and saved_window_geometry != "Default":
                self.restoreGeometry(QByteArray.fromBase64(saved_window_geometry.encode('utf-8')))
            if saved_window_state and saved_window_state != "Default":
                saved_window_state = QByteArray.fromBase64(saved_window_state.encode('utf-8'))
                self.restoreState(saved_window_state)
            if saved_window_geometry == "Default" or saved_window_state == "Default":
                self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
            self.restore_sidebar_states()

        else:
            self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.tts_editor.setFocus()

        apply_theme(settings_manager.get("SETTINGS/Theme"), self)

    def update_statusbar(self, text):
        self.statusbar.showMessage(text)

    def update_text_stats(self, text):        
        self.statusbar_text_stats.setText(text)



    def update_console_visibility(self):
        """
        Updates the visibility of the console's 'Log' tab and the tab bar
        based on the 'SETTINGS/ShowConsole' setting.
        """
        if not hasattr(self, 'console_tab_widget'):
             print("Error: console_tab_widget not initialized yet.") # Safety check
             return
        if not hasattr(self, 'consoleDockWidget'):
             print("Error: consoleDockWidget not initialized yet.") # Safety check
             return

        settings_manager = SettingsManager() # Get a fresh instance or use one stored in self if preferred
        show_console = settings_manager.get('SETTINGS/ShowConsole', 'false').lower() == 'true'


        # self.consoleDockWidget.setVisible(show_console)
        self.console_tab_widget.tabBar().setVisible(show_console)

        if hasattr(self, 'tb_bttn_console') and self.tb_bttn_console.isCheckable():
            self.tb_bttn_console.setChecked(show_console)

        log_tab_index = -1
        for i in range(self.console_tab_widget.count()):
            if self.console_tab_widget.widget(i) == self.log_tab:
                log_tab_index = i
                break

        if show_console:
            if log_tab_index == -1:
                if not hasattr(self, 'console_window'):
                    self.console_window = ConsoleWindow()
                    self.log_tab_layout.addWidget(self.console_window) # Add to layout if recreated
                    print("Warning: Recreated console_window in update_console_visibility")

                self.console_tab_widget.addTab(self.log_tab, " Log ")
            self.consoleDockWidget.setMinimumHeight(20) # Example minimum height
            self.consoleDockWidget.setMaximumHeight(600) # Example maximum height


        else:
            if log_tab_index != -1:
                self.console_tab_widget.removeTab(log_tab_index)
            player_height = self.audio_player_widget.sizeHint().height()
            target_height = player_height + 26 # Adjust padding as needed
            self.consoleDockWidget.setFixedHeight(target_height)


    def load_audio_file(self):
        output_file = self.tts_properties_window.outputFileEditBox.text()
        if output_file:
            self.audio_player_widget.load_file(output_file)

    def onTextModified(self):
        self.tts_editor.document().setModified(True)

    def closeEvent(self, event):
        self.tts_editor.textModified.connect(self.onTextModified)
        confirm_exit = settings_manager.get('SETTINGS/ConfirmExit') == "true"
        confirmTextModified = settings_manager.get('EDITOR/ConfirmTextModified') == "true"
        theme = settings_manager.get('SETTINGS/Theme')

        def setup_message_box(title, text, theme, standard_buttons):
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setStandardButtons(standard_buttons)
            icon_path = f'res\\{theme.lower()}\\question_fill.ico'
            box.setWindowIcon(QIcon(icon_path))
            question_icon_path = f'res\\{theme.lower()}\\question.ico'
            question_pixmap = QIcon(question_icon_path).pixmap(QSize(48, 48))
            box.setIconPixmap(question_pixmap)
            box.setText(text)
            return box

        if self.tts_editor.document().isModified() and confirmTextModified:
            box = setup_message_box('Unsaved Changes',
                                    'The document has been modified. Do you want to save your changes?',
                                    theme,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            message = box.exec()

            if message == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif message == QMessageBox.StandardButton.Yes:
                content = self.tts_editor.toPlainText()
                if hasattr(self, 'current_file') and self.current_file:
                    with open(self.current_file, 'w') as file:
                        file.write(content)
                    self.setWindowTitle(f"Usei - {self.current_file}")
                    # self._print(f"Saved to {self.current_file}")
                    global_signals.output_signal.emit(f"Saved to {self.current_file}")
                else:
                    file_dialog = QFileDialog(self)
                    file_dialog.setNameFilter("Text files (*.txt)")
                    file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
                    file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
                    if file_dialog.exec():
                        selected_file = file_dialog.selectedFiles()[0]
                        with open(selected_file, 'w') as file:
                            file.write(content)
                        self.setWindowTitle(f"Usei - {selected_file}")
                        # self._print(f"Saved to {selected_file}")
                        global_signals.output_signal.emit(f"Saved to {selected_file}")
                        self.current_file = selected_file

        elif confirm_exit:
            box = setup_message_box('Usei asks:',
                                    'Are you sure you want to exit?',
                                    theme,
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if box.exec() == QMessageBox.StandardButton.No:
                event.ignore()
                return

        if settings_manager.get('SETTINGS/SaveProgramSettings') == 'true':

            language = self.tts_properties_window.languageDropdown.currentText()
            voice = self.tts_properties_window.voicesDropdown.currentText()
            blending_checked = self.tts_properties_window.is_blending_checked()
            balance = self.tts_properties_window.blendSlider.value()
            blending_voice = self.tts_properties_window.blendingDropdown.currentText()
            speed = self.tts_properties_window.speedSpinBox.value()
            output_file = self.tts_properties_window.outputFileEditBox.text()
            wrapped = self.tb_bttn_wrap.isChecked()
            autoplay_checked = self.audio_player_widget.is_autoplay_checked()
            volume = self.audio_player_widget.volume_slider.value()

            # Save TTS settings
            settings_manager.set('TTS/Language', language)
            settings_manager.set('TTS/Voice', voice)
            settings_manager.set('TTS/Blending', blending_checked)
            settings_manager.set('TTS/BlendingVoice', blending_voice)
            settings_manager.set('TTS/BlendingBalance', balance)
            settings_manager.set('TTS/Speed', speed)
            settings_manager.set('TTS/OutputFile', output_file)


            # Save window geometry
            window_geometry = self.saveGeometry().toBase64().data().decode('utf-8')
            window_state = self.saveState().toBase64().data().decode('utf-8')
            settings_manager.set('SETTINGS/WindowGeometry', window_geometry)
            settings_manager.set('SETTINGS/WindowState', window_state)

            # Save dock widget geometry and visibility
            console_dock_geometry = self.consoleDockWidget.saveGeometry().toBase64().data().decode('utf-8')
            settings_manager.set('SETTINGS/ConsoleDockGeometry', console_dock_geometry)
            # settings_manager.set('SETTINGS/ConsoleDockVisible', self.consoleDockWidget.isVisible())

            llm_dock_geometry = self.TTSDockWidget.saveGeometry().toBase64().data().decode('utf-8')
            settings_manager.set('SETTINGS/TTSDockGeometry', llm_dock_geometry)
            settings_manager.set('SETTINGS/TTSDockVisible', self.TTSDockWidget.isVisible())

            # Update font size
            current_font_size = self.tts_editor.font().pointSize()
            settings_manager.set('EDITOR/FontSize', current_font_size)
            
            wrapped = self.tb_bttn_wrap.isChecked()  # Use boolean directly
            settings_manager.set("EDITOR/Wrapped", "true" if wrapped else "false")


            settings_manager.set('PLAYER/AutoPlay', autoplay_checked)
            settings_manager.set('PLAYER/Volume', volume)
            
        else:
            # Reset TTS settings if SaveProgramSettings is false
            settings_manager.reset_to_defaults()
            settings_manager.set('SETTINGS/WindowGeometry', None)
            settings_manager.set('SETTINGS/WindowState', None)
            settings_manager.set('SETTINGS/ConsoleDockGeometry', None)
            # settings_manager.set('SETTINGS/ConsoleDockVisible', None)
            settings_manager.set('SETTINGS/TTSDockGeometry', None)
            settings_manager.set('SETTINGS/TTSDockVisible', None)

        self.custom_tooltip = None
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        if self.custom_tooltip is not None:
            if obj.property("tooltip"):
                self.custom_tooltip.handle_event(obj, event)
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            selected_text = self.tts_editor.textCursor().selectedText()
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                show_search_dialog(self, 'expanded', selected_text)
            else:
                show_search_dialog(self, 'collapsed', selected_text)
        elif event.key() == Qt.Key.Key_F3 and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if not hasattr(self, 'search_dialog_instance'):
                self.search_dialog_instance = show_search_dialog(self, 'collapsed')
            if hasattr(self, 'search_dialog_instance') and self.search_dialog_instance.isVisible():
                self.search_dialog_instance.on_up_button_clicked()
        elif event.key() == Qt.Key.Key_F3:
            if not hasattr(self, 'search_dialog_instance'):
                self.search_dialog_instance = show_search_dialog(self, 'collapsed')
            if hasattr(self, 'search_dialog_instance') and self.search_dialog_instance.isVisible():
                self.search_dialog_instance.on_down_button_clicked()
            else:
                show_search_dialog(self, 'collapsed')
        elif event.key() == Qt.Key.Key_Escape:
            if not hasattr(self, 'search_dialog_instance'):
                self.search_dialog_instance = show_search_dialog(self, 'collapsed')
            if hasattr(self, 'search_dialog_instance') and self.search_dialog_instance.isVisible():
                self.search_dialog_instance.hide()
        else:
            super().keyPressEvent(event)

    def restore_sidebar_states(self):
        save_window_pos = settings_manager.get('SETTINGS/SaveProgramSettings') == 'true'

        # Restore window geometry and state
        if save_window_pos:
            window_geometry = settings_manager.get('SETTINGS/WindowGeometry')
            window_state = settings_manager.get('SETTINGS/WindowState')

            if window_geometry and window_geometry != 'None':
                self.restoreGeometry(QByteArray.fromBase64(window_geometry.encode('utf-8')))
            if window_state and window_state != 'None':
                self.restoreState(QByteArray.fromBase64(window_state.encode('utf-8')))

            console_dock_geometry = settings_manager.get('SETTINGS/ConsoleDockGeometry')
            if console_dock_geometry and console_dock_geometry != 'None':
                self.consoleDockWidget.restoreGeometry(QByteArray.fromBase64(console_dock_geometry.encode('utf-8')))

            llm_dock_geometry = settings_manager.get('SETTINGS/TTSDockGeometry')
            if llm_dock_geometry and llm_dock_geometry != 'None':
                self.TTSDockWidget.restoreGeometry(QByteArray.fromBase64(llm_dock_geometry.encode('utf-8')))

        else:
            # Default layout if SaveProgramSettings is not enabled
            self.resize(1200, 800)
            position_window(self, position="center")
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.TTSDockWidget)
            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.consoleDockWidget)


    def save_tts_dock_state(self):
        llm_dock_geometry = self.TTSDockWidget.saveGeometry().toBase64().data().decode('utf-8')
        settings_manager.set('SETTINGS/TTSDockGeometry', llm_dock_geometry)

    def restore_llm_dock_state(self):
        llm_dock_geometry = settings_manager.get('SETTINGS/TTSDockGeometry')
        if llm_dock_geometry:
            self.TTSDockWidget.restoreGeometry(QByteArray.fromBase64(llm_dock_geometry.encode('utf-8')))

    def reset_settings(self):
        settings_manager.reset_to_defaults()
        self.update_statusbar("Settings have been reset")
        global_signals.output_signal.emit("*** Settings have been reset \n")

    def change_theme(self):
        if settings_manager.get('SETTINGS/Theme') == 'Light':
            apply_theme('Dark', self)
            settings_manager.set('SETTINGS/Theme', 'Dark')
        else:
            apply_theme('Light', self)
            settings_manager.set('SETTINGS/Theme', 'Light')

        if hasattr(self, 'search_replace_dialog'):
            self.search_replace_dialog.update_icons()

    def show_settings(self, arg1=None):
        open_settings_window(self)


    def tb_click_function(self, name):
       
        if name == 'new_file':
            if self.tts_editor.document().isModified():
                box = QMessageBox(self)
                box.setWindowTitle('Unsaved Changes')
                box.setText('The document has been modified. Do you want to proceed?')
                box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if box.exec() == QMessageBox.StandardButton.No:
                    return
            self.tts_editor.clear()
            self.current_file = None
            self.setWindowTitle("Usei")

        elif name == 'open_file':
            if self.tts_editor.document().isModified():
                box = QMessageBox(self)
                box.setWindowTitle('Unsaved Changes')
                box.setText('The document has been modified. Do you want to proceed?')
                box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if box.exec() == QMessageBox.StandardButton.No:
                    return
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("Text files (*.txt)")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            if file_dialog.exec():
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    selected_file = selected_files[0]
                    with open(selected_file, 'r') as file:
                        content = file.read()
                    self.tts_editor.setPlainText(content)
                    self.current_file = selected_file
                    self.setWindowTitle(f"Usei - {selected_file}")
                    # self._print(f"Opened {selected_file}")
                    global_signals.output_signal.emit(f"Opened {selected_file}")
                else:
                    # self._print("No file selected")
                    global_signals.output_signal.emit("No file selected")
                    selected_file = None

        elif name == 'save':
            if hasattr(self, 'current_file') and self.current_file:
                content = self.tts_editor.toPlainText()
                with open(self.current_file, 'w') as file:
                    file.write(content)
                self.setWindowTitle(f"Usei - {self.current_file}")
                # self._print(f"Saved to {self.current_file}")
                global_signals.output_signal.emit(f"Saved to {self.current_file}")
            else:
                self.tb_click_function('save_as')

        elif name == 'save_as':
            file_dialog = QFileDialog(self)
            file_dialog.setNameFilter("Text files (*.txt)")
            file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            if file_dialog.exec():
                selected_file = file_dialog.selectedFiles()[0]
                content = self.tts_editor.toPlainText()
                with open(selected_file, 'w') as file:
                    file.write(content)
                self.setWindowTitle(f"Usei - {selected_file}")
                # self._print(f"Saved to {selected_file}")
                global_signals.output_signal.emit(f"Saved to {selected_file}")
                self.current_file = selected_file

        elif name == 'undo':
            self.tts_editor.undo()

        elif name == 'redo':
            self.tts_editor.redo()

        elif name == 'select_all':
            self.tts_editor.selectAllText()

        elif name == 'copy':
            self.tts_editor.copy()

        elif name == 'cut':
            self.tts_editor.cut()

        elif name == 'paste':
            self.tts_editor.paste()


        elif name == 'delete':
            self.tts_editor.delete()

        elif name == 'find':
            show_search_dialog(self, 'collapsed')

        elif name == 'replace':
            show_search_dialog(self, 'expanded')

        elif name == 'wrap':
            is_checked = self.tb_bttn_wrap.isChecked()
            wrapped_state = "true" if is_checked else "false"
            self.tts_editor.set_word_wrap(wrapped_state)

        elif name == 'settings':
            self.show_settings()

        elif name == 'console':
            current_state_bool = settings_manager.get('SETTINGS/ShowConsole', 'false').lower() == 'true'
            new_state_bool = not current_state_bool
            settings_manager.set('SETTINGS/ShowConsole', new_state_bool)
            self.update_console_visibility()

        elif name == 'about':
            self.about_window = AboutWindow()
            self.about_window.show()

        elif name == 'theme':
            self.change_theme()

    def find_next(self, text):
        self.tts_editor.find_text(text)

    def replace(self, text, replacement):
        self.tts_editor.replace_text(text, replacement)

    def replace_all(self, text, replacement):
        self.tts_editor.replace_all_text(text, replacement)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'search_replace_dialog') and self.search_replace_dialog.isVisible():
            editor_rect = self.tts_editor.geometry()
            toolbar_height = self.toolbar.height()
            self.search_replace_dialog.move(editor_rect.right() - self.search_replace_dialog.width() - 10, editor_rect.top() + toolbar_height + 1)

