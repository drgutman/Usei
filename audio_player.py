# audio_player.py
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QCheckBox, QToolButton
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import os
from utils import SettingsManager, CustomSlider
from signals import global_signals
import shutil

settings_manager = SettingsManager()
os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.ffmpeg=false'

class AudioPlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.init_ui()
        self.init_media()

        self.reset_player_state()
        
        global_signals.addChunkToPlayerSignal.connect(self.add_to_playlist)
        global_signals.fused_file_completed.connect(self.handle_fused_file_update)
        global_signals.new_render_started.connect(self.reset_player_state)

        self.fused_file_loaded = False
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()
        theme = settings_manager.get('SETTINGS/Theme').lower()

        self.play_button = QPushButton()
        self.play_button.setFixedSize(26, 26)
        self.play_button.setIcon(QIcon(os.path.join('res', theme, 'play.ico')))
        self.play_button.clicked.connect(self.toggle_play_pause)

        self.stop_button = QPushButton()
        self.stop_button.setFixedSize(26, 26)
        self.stop_button.setIcon(QIcon(os.path.join('res', theme, 'stop.ico')))
        self.stop_button.clicked.connect(self.stop_playback)

        self.seek_bar = QSlider(Qt.Orientation.Horizontal)
        self.seek_bar.setRange(0, 0)
        self.seek_bar.sliderMoved.connect(self.set_position)

        self.seek_bar.setStyleSheet("""
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

        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")

        self.mute_button = QToolButton()
        self.play_button.setCheckable(True)
        self.mute_button.setFixedSize(24, 24)
        self.mute_button.setIcon(QIcon(os.path.join('res', theme, 'vol_high.ico')))  
        self.mute_button.clicked.connect(self.toggle_mute)

        self.volume_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(50) 

        remember_volume = settings_manager.get('PLAYER/Volume')
        self.volume_slider.setValue(remember_volume)
        self.audio_output.setVolume(remember_volume / 100)
        self.volume_slider.valueChanged.connect(self.update_volume)

        self.autoplay_checkbox = QCheckBox("Autoplay")

        for w in (self.play_button, self.stop_button, self.current_time_label,
                self.seek_bar, self.total_time_label, self.mute_button, self.volume_slider, self.autoplay_checkbox):
            control_layout.addWidget(w)

        remember_autoplay = settings_manager.get('PLAYER/AutoPlay')
        self.autoplay_checkbox.setChecked(remember_autoplay.lower() == 'true')
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)

    def reset_player_state(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_playback()
        else:
            self.playlist_files = []
            self.player.setSource(QUrl())
            self.current_index = 0
            self.fused_file_path = ""
            self.fused_file_finished = False
            self.fused_file_message = ""
            self.seek_bar.setValue(0)
            self.current_time_label.setText("00:00")
            self.player.blockSignals(True)
            self.player.stop()
            self.player.blockSignals(False)
            self.fused_file_loaded = False

    def load_file(self, file_path, stop_before_loading=True):
        # Load a single file directly, replacing current playlist
        if not os.path.exists(file_path):
            print(f"Warning: File does not exist: {file_path}")
            return
        if stop_before_loading:
            self.stop_playback()  # This will call on_playlist_finished if needed
        self.playlist_files = [file_path]
        self.current_index = 0
        self.player.setSource(QUrl.fromLocalFile(file_path))
        if self.autoplay_checkbox.isChecked():
            self.player.play()


    def add_to_playlist(self, file_path):
        if not os.path.exists(file_path):
            print(f"Warning: Cannot add non-existent file to playlist: {file_path}")
            return

        self.playlist_files.append(file_path)
        print(f"Added to playlist: {file_path}")

        if len(self.playlist_files) == 1:
            self.current_index = 0
            self.load_current_file()

    def load_current_file(self):
        if self.current_index < len(self.playlist_files) and os.path.exists(self.playlist_files[self.current_index]):
            current_file = self.playlist_files[self.current_index]
            self.player.setSource(QUrl.fromLocalFile(current_file))
            print(f"Loading file #{self.current_index}: {current_file}")
            if self.autoplay_checkbox.isChecked():
                self.player.play()


    def handle_fused_file_update(self, success, message, temp_folder):
        self.fused_file_finished = success
        self.temp_folder_to_clean = temp_folder

        if isinstance(message, str) and os.path.exists(message):
            self.fused_file_path = message
        else:
            print(f"Fusion failed: {message}")

    def init_media(self):
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if getattr(self, 'media_end_handled', False):
                return
            print(f"End of media for file #{self.current_index}")
            if self.current_index < len(self.playlist_files) - 1:
                self.current_index += 1
                self.load_current_file()
            else:
                # Last chunk finished.
                self.on_playlist_finished()

    def cleanup_temp_files(self, temp_folder):
        if temp_folder and os.path.exists(temp_folder):
            try:
                shutil.rmtree(temp_folder)
                print(f"Cleaned up temporary folder: {temp_folder}")
            except Exception as e:
                print(f"Cleanup error: {str(e)}")

    def on_playlist_finished(self):
        # Load fused file if available
        if self.fused_file_finished and os.path.exists(self.fused_file_path):
            if self.player.source().toLocalFile() != self.fused_file_path:
                print(f"Loading fused file: {self.fused_file_path}")
                self.load_file(self.fused_file_path, stop_before_loading=False)
                self.player.pause()
                self.fused_file_loaded = True

        # Only clean up if we have a temp folder and haven't cleaned yet
        if self.temp_folder_to_clean:
            self.cleanup_temp_files(temp_folder=self.temp_folder_to_clean)
            self.temp_folder_to_clean = None

    def update_duration(self, duration):
        self.seek_bar.setRange(0, duration)
        self.total_time_label.setText(self.format_time(duration))

    def update_position(self, position):
        self.seek_bar.setValue(position)
        self.current_time_label.setText(self.format_time(position))

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop_playback(self):
        self.player.stop()
        # If fused file is ready and not loaded yet, load it and clean up.
        if self.fused_file_finished and self.fused_file_path and os.path.exists(self.fused_file_path) and not self.fused_file_loaded:
            self.on_playlist_finished()

    def on_playback_state_changed(self, state):
        theme = settings_manager.get('SETTINGS/Theme').lower()
        icon = 'pause.ico' if state == QMediaPlayer.PlaybackState.PlayingState else 'play.ico'
        self.play_button.setIcon(QIcon(os.path.join('res', theme, icon)))

    def set_position(self, position):
        self.player.setPosition(position)

    def format_time(self, milliseconds):
        minutes, seconds = divmod(milliseconds // 1000, 60)
        return f"{minutes:02}:{seconds:02}"

    def is_autoplay_checked(self):
        return self.autoplay_checkbox.isChecked()

    def toggle_mute(self):
        theme = settings_manager.get('SETTINGS/Theme').lower()
        if self.audio_output.isMuted():
            self.audio_output.setMuted(False)
            self.mute_button.setIcon(QIcon(os.path.join('res', theme, 'vol_high.ico')))
        else:
            self.audio_output.setMuted(True)
            self.mute_button.setIcon(QIcon(os.path.join('res', theme, 'mute.ico')))

    def update_volume(self, value):
        self.audio_output.setVolume(value / 100)

