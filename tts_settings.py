from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import QLineEdit, QScrollArea, QFrame, QWidget, QFileDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QDoubleSpinBox, QSlider, QMessageBox, QCheckBox

import os
from utils import SettingsManager, OverlayWidget
from signals import global_signals
from tooltips import ToolTips
from tts_render import render_text




settings_manager = SettingsManager()

from tts_render import render_text


class TTSPropertiesWindow(QWidget):


    global_signals = global_signals

    def __init__(self, tts_editor, audio_player):
        super(TTSPropertiesWindow, self).__init__()

        global_signals.toggleGifSignal.connect(self.toggleLoadingGif)

        self.audio_player = audio_player
        self.tts_editor = tts_editor
        self.active_threads = []

        self.setMinimumHeight(220)
        self.setMinimumWidth(280)

        main_frame = QFrame(self)
        main_frame.setObjectName("mainFrame")

        self.custom_tooltip = ToolTips()

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        frame_layout.addWidget(scroll_area)

        scroll_container = QWidget()
        scroll_area.setWidget(scroll_container)
        container_layout = QVBoxLayout(scroll_container)
        container_layout.setContentsMargins(4, 0, 8, 0)
        container_layout.setSpacing(0)



        settingsLayout = QVBoxLayout()
        settingsLayout.setSpacing(0)

        ###### LANGUAGE DROPDOWN ######

        self.languageLabel = QLabel("Language:")
        self.languageLabel.setObjectName("LanguageLabel")
        self.languageLabel.setFixedWidth(70)

        self.languageDropdown = QComboBox()
        self.languageDropdown.setPlaceholderText("Select language")
        self.languageDropdown.setObjectName("LanguageDropdown")
        self.languageDropdown.currentIndexChanged.connect(self.update_voices_dropdown)
        self.languageDropdown.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(125, 125, 125, 1);
                padding: 0px 0px 0px 5px; margin: 0px;
                background-color: rgba(125, 125, 125, 0.1);
            }
            QComboBox::indicator {
                background-color: #666666;
            }
            QComboBox::indicator:checked {
                background-color: rgba(180, 180, 180, 0.3);
            }
        """)
        voices = ['af_alloy', 
                  'af_aoede', 
                  'af_bella', 
                  'af_heart', 
                  'af_jessica', 
                  'af_kore', 
                  'af_nicole', 
                  'af_nova', 
                  'af_river', 
                  'af_sarah', 
                  'af_sky', 
                  'am_adam', 
                  'am_echo', 
                  'am_eric', 
                  'am_fenrir', 
                  'am_liam', 
                  'am_michael', 
                  'am_onyx', 
                  'am_puck', 
                  'am_santa', 
                  'bf_alice', 
                  'bf_emma', 
                  'bf_isabella', 
                  'bf_lily', 
                  'bm_daniel', 
                  'bm_fable', 
                  'bm_george', 
                  'bm_lewis', 
                  'ff_siwis', 
                  'if_sara', 
                  'im_nicola', 
                  'ef_dora', 
                  'em_alex', 
                  'em_santa', 
                  'hf_alpha', 
                  'hf_beta', 
                  'hm_omega', 
                  'hm_psi', 
                  'jf_alpha', 
                  'jf_gongitsune', 
                  'jf_nezumi', 
                  'jf_tebukuro', 
                  'jm_kumo', 
                  'pf_dora', 
                  'pm_alex', 
                  'pm_santa', 
                  'zf_xiaobei', 
                  'zf_xiaoni', 
                  'zf_xiaoxiao', 
                  'zf_xiaoyi']

        # Extract unique language codes while preserving order
        language_codes = []
        for voice in voices:
            if voice[:1] not in language_codes:
                language_codes.append(voice[:1])

        # Map language codes to full language names
        language_mapping = {
            'a': 'American English',
            'b': 'British English',
            'j': 'Japanese',
            'z': 'Mandarin Chinese',
            'e': 'Spanish',
            'f': 'French',
            'h': 'Hindi',
            'i': 'Italian',
            'p': 'Brazilian Portuguese'
        }

        # Populate language dropdown
        for code in language_codes:
            if code in language_mapping:
                self.languageDropdown.addItem(language_mapping[code], userData=code)

        self.languageDropdown.setCurrentIndex(-1)

        languageLayout = QHBoxLayout()
        languageLayout.setContentsMargins(0, 14, 0, 4)
        languageLayout.setSpacing(5)
        languageLayout.addWidget(self.languageLabel)
        languageLayout.addWidget(self.languageDropdown)
        settingsLayout.addLayout(languageLayout)

        ###### VOICE DROPDOWN ######
        voiceLayout = QHBoxLayout()
        voiceLayout.setContentsMargins(0, 4, 0, 4)
        voiceLayout.setSpacing(5)

        self.voiceLabel = QLabel("Voice:")
        self.voiceLabel.setObjectName("VoiceLabel")
        self.voiceLabel.setFixedWidth(70)

        self.voicesDropdown = QComboBox()
        self.voicesDropdown.setPlaceholderText("First select language.")
        self.voicesDropdown.setObjectName("VoiceDropdown")
        self.voicesDropdown.setEnabled(False)

        self.voicesDropdown.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(125, 125, 125, 1);
                padding: 0px 0px 0px 5px; margin: 0px;
                background-color: rgba(125, 125, 125, 0.1);
            }
            QComboBox::indicator {
                background-color: #666666;
            }
            QComboBox::indicator:checked {
                background-color: rgba(180, 180, 180, 0.3);
            }
        """)


        voiceLayout.addWidget(self.voiceLabel)
        voiceLayout.addWidget(self.voicesDropdown)
        settingsLayout.addLayout(voiceLayout)

        ###### VOICE BLENDING ######

        # Blending checkbox layout
        self.blendingCheckLayout = QHBoxLayout()
        self.blendingCheckLayout.setContentsMargins(2, 4, 2, 8)

        # Blending checkbox
        self.blending_check = QCheckBox("Use voice blending.")
        self.blending_check.toggled.connect(self.onBlendingCheckToggled)
        self.blendingCheckLayout.addWidget(self.blending_check)

        # if language has only one voice set blending check to disabled

        # Blending content layout
        self._blending_content = QWidget()
        self._blending_content_layout = QVBoxLayout(self._blending_content)
        self._blending_content_layout.setContentsMargins(0, 0, 0, 12)
        self._blending_content_layout.setSpacing(0)

        self.blendVoiceLayout = QHBoxLayout()
        self.blendVoiceLayout.setContentsMargins(0, 4, 0, 4)
        self.blendVoiceLayout.setSpacing(5)

        # Blending label
        self.blendingLabel = QLabel("2nd Voice:")
        self.blendingLabel.setObjectName("BlendingLabel")
        self.blendingLabel.setFixedWidth(70)


        self.blendingLabel = QLabel("2nd Voice:")
        self.blendingLabel.setObjectName("BlendingLabel")
        self.blendingLabel.setFixedWidth(70)

        self.blendingDropdown = QComboBox()
        self.blendingDropdown.setPlaceholderText("Select 2nd voice.")
        self.blendingDropdown.setObjectName("BlendingDropdown")
        self.blendingDropdown.setEnabled(False)

        self.blendingDropdown.setStyleSheet("""
            QComboBox {

                border: 1px solid rgba(125, 125, 125, 1);
                padding: 0px 0px 0px 5px; margin: 0px;
                background-color: rgba(125, 125, 125, 0.1);
            }
            QComboBox::indicator {

                background-color: #666666;
            }
            QComboBox::indicator:checked {
                background-color: rgba(180, 180, 180, 0.3);
            }
        """)

        self.blendVoiceLayout.addWidget(self.blendingLabel)
        self.blendVoiceLayout.addWidget(self.blendingDropdown)

        self.blendRatioLayout = QHBoxLayout()
        self.blendRatioLayout.setContentsMargins(0, 4, 0, 4)
        self.blendRatioLayout.setSpacing(5)

        self.ratioLabel = QLabel("Blend Ratio:")
        self.ratioLabel.setObjectName("RatioLabel")
        self.ratioLabel.setFixedWidth(70)
        self.blendRatioLayout.addWidget(self.ratioLabel)

        # Set up the slider with the correct range and starting value
        self.blendSlider = QSlider(Qt.Orientation.Horizontal)
        self.blendSlider.setRange(0, 100)
        # self.blendSlider.setValue(50)
        self.blendSlider.setSingleStep(1)
        self.blendSlider.setPageStep(1)

        self.blendRatioLayout.addWidget(self.blendSlider)

        self.blendSlider.setStyleSheet("""
            QSlider {  padding: 0px; margin: 0px; }
            QSlider::groove:horizontal {
                border: 1px solid rgba(128, 128, 128, 0.1);
                height: 8px;
                margin: 0px 0;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);;
                border: 1px solid rgba(128, 128, 128, 0.1);
                height: 10px;
                width: 6px;
                margin: -4 -2 -4 -2;
            }

            QSlider::sub-page:horizontal {
                background: rgba(128, 128, 128, 0.8);
                height: 6px;
            }
        """)



        self._blending_content_layout.addLayout(self.blendVoiceLayout)
        self._blending_content_layout.addLayout(self.blendRatioLayout)

        

        # Initially set the visibility based on the checkbox state
        self._blending_content.setVisible(self.blending_check.isChecked())

        # Add blending content to the settings layout
        settingsLayout.addLayout(self.blendingCheckLayout)
        settingsLayout.addWidget(self._blending_content)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("margin-left: 30px; margin-right: 30px;")
        settingsLayout.addWidget(separator)

        # Store voices for dynamic population
        self.voices = voices
        
        ###### SPEED SLIDER ######
        speedLayout = QHBoxLayout()
        speedLayout.setContentsMargins(0, 14, 0, 14)
        speedLayout.setSpacing(5)

        speedLabel = QLabel("Speed:")
        speedLabel.setObjectName("SpeedLabel")
        speedLabel.setFixedWidth(70)
        speedLayout.addWidget(speedLabel)

        # Set up the slider with the correct range and starting value
        self.speedSlider = QSlider(Qt.Orientation.Horizontal)
        self.speedSlider.setRange(5, 20)
        self.speedSlider.setValue(5)
        self.speedSlider.setSingleStep(1)
        self.speedSlider.setPageStep(1)

        speedLayout.addWidget(self.speedSlider)

        self.speedSlider.setStyleSheet("""
            QSlider {  padding: 0px; margin: 0px; }
            QSlider::groove:horizontal {
                border: 1px solid rgba(128, 128, 128, 0.1);
                height: 8px;
                margin: 0px 0;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);;
                border: 1px solid rgba(128, 128, 128, 0.1);
                height: 10px;
                width: 6px;
                margin: -4 -2 -4 -2;
            }

            QSlider::sub-page:horizontal {
                background: rgba(128, 128, 128, 0.8);
                height: 6px;
            }
        """)

        # Set up the spinbox with the correct range and precision
        self.speedSpinBox = QDoubleSpinBox()
        self.speedSpinBox.setStyleSheet("QDoubleSpinBox {border-color: rgba(125, 125, 125, 1);}")
        self.speedSpinBox.setRange(0.5, 2.0)
        self.speedSpinBox.setSingleStep(0.1)
        self.speedSpinBox.setDecimals(1)
        self.speedSpinBox.setValue(0.5)
        self.speedSpinBox.setFixedWidth(54)

        speedLayout.addWidget(self.speedSpinBox)

        # Connect signals
        self.speedSlider.valueChanged.connect(self.updateSpinBoxFromSlider)
        self.speedSpinBox.valueChanged.connect(self.updateSliderFromSpinBox)

        settingsLayout.addLayout(speedLayout)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("margin-left: 30px; margin-right: 30px;")
        settingsLayout.addWidget(separator)

        ###### RENDER OUTPUT ######

        renderOutputLayout = QHBoxLayout()
        renderOutputLayout.setContentsMargins(0, 14, 0, 8)
        # renderOutputLayout.setSpacing(5)

        renderOutputLabel = QLabel("Output:")
        renderOutputLabel.setObjectName("OutputFileLabel")
        renderOutputLabel.setFixedWidth(70)
        renderOutputLayout.addWidget(renderOutputLabel)

        self.outputFileEditBox = QLineEdit()
        self.outputFileEditBox.setObjectName("OutputFileEditBox")
        self.outputFileEditBox.setPlaceholderText("Select output file ...")
        self.outputFileEditBox.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(125, 125, 125, 1);
                padding: 0px 0px 0px 5px; 
                background-color: rgba(125, 125, 125, 0.1);
                }
        """)
        


        self.outputFileEditBox.setFixedHeight(26)
        renderOutputLayout.addWidget(self.outputFileEditBox)

        self.browseButton = QPushButton("...")

        self.browseButton.setStyleSheet("QPushButton {border-left: none; margin: 0px; padding: 0; background-color: rgba(125, 125, 125, 0.2)}")
        self.browseButton.setFixedSize(20, 26)
        self.browseButton.clicked.connect(self.browseButtonClicked)

        renderOutputLayout.addWidget(self.browseButton)
        settingsLayout.addLayout(renderOutputLayout)

        ###### RENDER OUTPUT ######################################################################

        ###### RENDER BUTTON ######

        self.RenderButton = QPushButton(" Render ")
        self.RenderButton.setMinimumHeight(28)
        self.RenderButton.setMinimumWidth(180)
        self.RenderButton.clicked.connect(self.renderButtonClicked)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(0, 10, 0, 4)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.RenderButton)
        buttonLayout.addStretch()
        settingsLayout.addLayout(buttonLayout)

        ###### WAITING/WORKING ANIMATION WIDGET ######

        # Create and setup the overlay widget
        self.overlay = OverlayWidget(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.hide()  # Hide initially

        # Create a frame for the GIF with a semi-transparent background
        self.gifFrame = QFrame(self.overlay)
        self.gifFrame.setStyleSheet("background-color: rgba(20, 20, 20, 0.5);")  # Semi-transparent gray
        self.gifFrame.hide()  # Hide initially

        # Setup for the loading GIF within the frame
        self.loadingGifLabel = QLabel(self.gifFrame)
        movie = QMovie("res/wait_.gif")
        self.loadingGifLabel.setMovie(movie)
        self.loadingGifLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Load TTS settings
        language = settings_manager.get('TTS/Language')
        voice = settings_manager.get('TTS/Voice')
        blending = settings_manager.get('TTS/Blending')
        blend_voice = settings_manager.get('TTS/BlendingVoice')
        balance = settings_manager.get('TTS/BlendingBalance')
        speed = settings_manager.get('TTS/Speed')
        output_file = settings_manager.get('TTS/OutputFile')
        if language:
            self.languageDropdown.setCurrentText(language)
        if voice:
            self.voicesDropdown.setCurrentText(voice)
        if blending:
            self.blending_check.setChecked(blending.lower() == 'true')
        if blend_voice:
            self.blendingDropdown.setCurrentText(blend_voice)
        if balance:
            self.blendSlider.setValue(int(balance))
        if speed:
            self.speedSpinBox.setValue(float(speed))
        if output_file:
            self.outputFileEditBox.setText(output_file)
            self.outputFileEditBox.setText(output_file)



        container_layout.addLayout(settingsLayout)
        container_layout.addStretch()
        # container_layout.setMinimumWidth(240)

    
    def is_blending_checked(self):
        return self.blending_check.isChecked()
    

    def onBlendingCheckToggled(self, checked):
        self._blending_content.setVisible(checked)

    def positionLoadingGif(self):
        """ Position the loading GIF over the desired area """
        gif_size = QSize(100, 100)  # Set the size of the GIF

        # Calculate the position to center the GIF in the parent widget
        parent_rect = self.rect()
        center_x = parent_rect.width() // 2 - gif_size.width() // 2
        center_y = parent_rect.height() // 2 - gif_size.height() // 2

        # Set the geometry of the GIF label relative to the parent widget
        self.loadingGifLabel.setGeometry(center_x, center_y, gif_size.width(), gif_size.height())
        self.loadingGifLabel.raise_()  # Raise above other widgets

    def resizeEvent(self, event):
        super(TTSPropertiesWindow, self).resizeEvent(event)
        self.overlay.setGeometry(0, 0, self.width(), self.height())

        # Calculate new position and size for the GIF and its frame
        gif_size = QSize(100, 100)  # Size of the GIF
        gif_x = (self.width() - gif_size.width()) // 2
        gif_y = (self.height() - gif_size.height()) // 2 - 40  # Move up by 40 pixels

        self.gifFrame.setGeometry(gif_x, gif_y, gif_size.width(), gif_size.height())
        self.loadingGifLabel.setGeometry(0, 0, gif_size.width(), gif_size.height())

    def toggleLoadingGif(self):
        """ Toggle the visibility of the loading GIF """
        if self.overlay.isVisible():
            self.loadingGifLabel.movie().stop()
            self.overlay.hide()
            self.gifFrame.hide()
        else:
            self.loadingGifLabel.movie().start()
            self.overlay.show()
            self.gifFrame.show()


    def renderButtonClicked(self):
        text = self.tts_editor.toPlainText().strip()
        speed = self.speedSpinBox.value()
        language = self.languageDropdown.currentText()
        voice = self.voicesDropdown.currentData()
        output_file = self.outputFileEditBox.text()
        blend_voice = self.blendingDropdown.currentData()
        blend_balance = self.blendSlider.value()

        missing_params = []
        if not text:
            missing_params.append("Text")
        if not language:
            missing_params.append("Language")
        if not voice:
            missing_params.append("Voice")
        if self.blending_check.isChecked() and not blend_voice:
            missing_params.append("Secondary voice")
        if not output_file:
            missing_params.append("Output File")

        if missing_params:
            box = QMessageBox(self)
            box.setWindowTitle("Missing Parameters")
            box.setText(f"The following parameters are missing: {', '.join(missing_params)}.")
            box.setStandardButtons(QMessageBox.StandardButton.Ok)
            box.setStyleSheet("QPushButton { margin: 0px; }")
            box.exec()
            return
        else:
            # Check if the output directory exists
            output_dir = os.path.dirname(output_file)
            if not os.path.isdir(output_dir) or not output_dir:
                QMessageBox.warning(
                    self,
                    "Invalid Output Path",
                    f"The directory for the output file does not exist. Please choose a valid output file path."
                )
                return

            # Proceed with existing file handling
            if os.path.exists(output_file):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("File Exists")
                msg_box.setText(f"The file '{output_file}' already exists. What would you like to do?")
                overwrite_button = msg_box.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
                save_new_button = msg_box.addButton("Save as New Name", QMessageBox.ButtonRole.ActionRole)
                cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                msg_box.setDefaultButton(overwrite_button)
                msg_box.exec()

                if msg_box.clickedButton() == cancel_button:
                    return
                elif msg_box.clickedButton() == save_new_button:
                    def get_unique_filename(file_path):
                        dir_name = os.path.dirname(file_path)
                        base_name = os.path.basename(file_path)
                        name, ext = os.path.splitext(base_name)
                        counter = 1
                        while True:
                            new_name = f"{name}_{counter:05d}{ext}"
                            new_path = os.path.join(dir_name, new_name)
                            if not os.path.exists(new_path):
                                return new_path
                            counter += 1
                    output_file = get_unique_filename(output_file)

            # Now proceed with rendering
            if self.blending_check.isChecked():
                render_text(
                    context=self,
                    text=text,
                    voice=voice,
                    language=language,
                    speed=speed,
                    output_file=output_file,
                    blend_voice=blend_voice,
                    blend_balance=blend_balance
                )
            else:
                render_text(
                    context=self,
                    text=text,
                    voice=voice,
                    language=language,
                    speed=speed,
                    output_file=output_file,
                )
            print(f"Output: {output_file}")


            
    # def renderButtonClicked(self):
    #     text = self.tts_editor.toPlainText().strip()
    #     speed = self.speedSpinBox.value()
    #     language = self.languageDropdown.currentText()
    #     voice = self.voicesDropdown.currentData()
    #     output_file = self.outputFileEditBox.text()
    #     blend_voice = self.blendingDropdown.currentData()
    #     blend_balance = self.blendSlider.value()

    #     missing_params = []
    #     if not text:
    #         missing_params.append("Text")
    #     if not language:
    #         missing_params.append("Language")
    #     if not voice:
    #         missing_params.append("Voice")
    #     if self.blending_check.isChecked() and not blend_voice:
    #         missing_params.append("Secondary voice")
    #     if not output_file:
    #         missing_params.append("Output File")

    #     if missing_params:
    #         box = QMessageBox(self)
    #         box.setWindowTitle("Missing Parameters")
    #         box.setText(f"The following parameters are missing: {', '.join(missing_params)}.")
    #         box.setStandardButtons(QMessageBox.StandardButton.Ok)
    #         box.setStyleSheet("QPushButton { margin: 0px; }")
    #         box.exec()
    #         return
    #     else:
    #         # Check if output file exists and handle accordingly
    #         if os.path.exists(output_file):
    #             # Inside your renderButtonClicked function:
    #             msg_box = QMessageBox(self)
    #             msg_box.setWindowTitle("File Exists")
    #             msg_box.setText(f"The file '{output_file}' already exists. What would you like to do?")

    #             # Correct way to add buttons in PyQt6
    #             overwrite_button = msg_box.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
    #             save_new_button = msg_box.addButton("Save as New Name", QMessageBox.ButtonRole.ActionRole)
    #             cancel_button = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

    #             msg_box.setDefaultButton(overwrite_button)
    #             msg_box.exec()

    #             if msg_box.clickedButton() == cancel_button:
    #                 return
    #             elif msg_box.clickedButton() == save_new_button:
    #                 # Function to generate unique filename
    #                 def get_unique_filename(file_path):
    #                     dir_name = os.path.dirname(file_path)
    #                     base_name = os.path.basename(file_path)
    #                     name, ext = os.path.splitext(base_name)
    #                     counter = 1
    #                     while True:
    #                         new_name = f"{name}_{counter:05d}{ext}"
    #                         new_path = os.path.join(dir_name, new_name)
    #                         if not os.path.exists(new_path):
    #                             return new_path
    #                         counter += 1
    #                 output_file = get_unique_filename(output_file)

    #         # Proceed with rendering using the determined output_file
    #         if self.blending_check.isChecked():
    #             render_text(
    #                 context=self,
    #                 text=text,
    #                 voice=voice,
    #                 language=language,
    #                 speed=speed,
    #                 output_file=output_file,
    #                 blend_voice=blend_voice,
    #                 blend_balance=blend_balance
    #             )
    #         else:
    #             render_text(
    #                 context=self,
    #                 text=text,
    #                 voice=voice,
    #                 language=language,
    #                 speed=speed,
    #                 output_file=output_file,
    #             )
    #         print(f"Output: {output_file}")
            
    def browseButtonClicked(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilter("Audio files (*.wav *.mp3)")
        file_dialog.setDefaultSuffix("wav")
        file_dialog.selectFile("output.wav")

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.outputFileEditBox.setText(file_path)

    ###### SPEED SLIDER HELPER FUNCTIONS ######

    def updateSpinBoxFromSlider(self, value):
        self.speedSpinBox.blockSignals(True)
        self.speedSpinBox.setValue(value / 10.0)
        self.speedSpinBox.blockSignals(False)

    def updateSliderFromSpinBox(self, value):
        self.speedSlider.blockSignals(True)
        self.speedSlider.setValue(int(value * 10))
        self.speedSlider.blockSignals(False)


    def update_voices_dropdown(self, index):
        current_language_code = self.languageDropdown.itemData(index)
        self.voicesDropdown.clear()
        self.voicesDropdown.setEnabled(True)
        self.blendingDropdown.clear()
        self.blendingDropdown.setEnabled(True)

        # Ensure the voice filtering is done correctly
        filtered_voices = [voice for voice in self.voices if voice.startswith(current_language_code)]

        for voice in filtered_voices:
            # Adjust how the voice name is extracted
            voice_parts = voice.split('_')
            if len(voice_parts) > 1:
                voice_name = voice_parts[1].capitalize()
                gender = "Female" if "f" in voice else "Male"
                display_name = f"{voice_name} ({gender.lower()})"
                self.voicesDropdown.addItem(display_name, userData=voice)
                self.blendingDropdown.addItem(display_name, userData=voice)

        if len(filtered_voices) > 1:
            self.blending_check.setEnabled(True)
        else:
            self.blending_check.setEnabled(False)
            self.blending_check.setChecked(False)  # Uncheck if disabled
            self._blending_content.setVisible(False)  # Hide blending controls if visible

    def is_autoplay_checked(self):
        return self.autoplay_checkbox.isChecked()

    def updateSpeedValue(self, value):
        self.speedSpinBox.setValue(value / 10.0)

    def updateSpeedSlider(self, value):
        self.speedSlider.setValue(int(value * 10))

