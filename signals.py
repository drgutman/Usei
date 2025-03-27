# signals.py
from PyQt6.QtCore import QObject, pyqtSignal

class GlobalSignals(QObject):
    output_signal = pyqtSignal(str)
    statusbar_signal = pyqtSignal(str)
    text_stats_signal = pyqtSignal(str)

    new_render_started = pyqtSignal()
    addChunkToPlayerSignal = pyqtSignal(str)
    fused_file_completed = pyqtSignal(bool, str, str)

    startAnimationSignal = pyqtSignal()  # signal to start the spinner
    stopAnimationSignal = pyqtSignal()   # signal to stop the spinner
    toggleGifSignal = pyqtSignal()   # signal to stop the spinner

    loading_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    files_ready = pyqtSignal()
    error_signal = pyqtSignal(str)

global_signals = GlobalSignals()

