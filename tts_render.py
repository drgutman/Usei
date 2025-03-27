# tts_render.py
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import os
import builtins
import shutil
import re
from functools import partial


from signals import global_signals
from utils import settings_manager, split_text_into_chunks
import uuid
# from pydub import AudioSegment

class RenderChunksThread(QThread):
    chunk_ready = pyqtSignal(str)
    finished = pyqtSignal(str, str)

    def __init__(self, text, voice, speed, language, kokoro_instance, is_phonemes, temp_folder, output_file, blend_voice=None, blend_balance=None):
        super().__init__()

        self.text = text
        self.voice = voice
        self.speed = speed
        self.language = language
        self.kokoro = kokoro_instance
        self.is_phonemes = is_phonemes
        self.blend_voice = blend_voice
        self.blend_balance = blend_balance
        self.output_file = output_file

        self.temp_folder = temp_folder
        self.chunk_files = []
        self._is_cancelled = False

    def run(self):
        chunks = split_text_into_chunks(self.text)
        self.chunk_files = []
        language_mapping = {
            'American English': 'en-us',
            'British English': 'en-gb',
            'Japanese': 'ja',
            'French': 'fr-fr',
            'Spanish': 'es',
            'Italian': 'it',
            'Hindi': 'hi',
            'Brazilian Portuguese': 'pt-br',
            'Mandarin Chinese': 'zh',
        }
        language_code = language_mapping.get(self.language, 'en-us')

        for i, chunk in enumerate(chunks):
            try:
                if self.language in ('American English', 'British English'):
                    phonemes = chunk
                    is_phonemes = False
                elif language_code == 'ja':
                    if re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', chunk):
                        # Contains Japanese characters: use the dedicated G2P
                        g2p = builtins.ja_g2p_instance
                        result = g2p(chunk)
                        # If result is a tuple, extract the first element; otherwise use the result as is.
                        phonemes = result[0] if isinstance(result, tuple) else result
                        is_phonemes = True
                        if not phonemes:
                            self.finished.emit(f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence", "")
                            return
                    else:
                        # Romanized Japanese: treat as text for espeak conversion
                        phonemes = chunk
                        is_phonemes = False


                elif language_code == 'zh':
                    g2p = builtins.zh_g2p_instance
                    phonemes, _ = g2p(chunk)
                    if not phonemes:
                        self.finished.emit(f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence", "")
                        return
                    is_phonemes = True
                else:
                    g2p = builtins.g2p_instance(language=language_code)
                    phonemes, _ = g2p(chunk)
                    if not phonemes:
                        self.finished.emit(f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence", "")
                        return
                    is_phonemes = True

                voice_to_use = self.voice
                if self.blend_voice and self.blend_balance is not None:
                    primary_voice = self.kokoro.get_voice_style(self.voice)
                    secondary_voice = self.kokoro.get_voice_style(self.blend_voice)
                    voice_to_use = builtins.np.add(primary_voice * ((100 - self.blend_balance) / 100), secondary_voice * (self.blend_balance / 100))

                samples, sample_rate = self.kokoro.create(phonemes, voice=voice_to_use, speed=self.speed, is_phonemes=is_phonemes)
                out_file = os.path.join(self.temp_folder, f"chunk_{i:03d}.wav")
                builtins.sf.write(out_file, samples, sample_rate)
                self.chunk_files.append(out_file)
                self.chunk_ready.emit(out_file)
                global_signals.statusbar_signal.emit(f"Temporary file chunk_{i:03d}.wav finished")

                if self._is_cancelled:
                    self.cleanup_partial_files()
                    return Exception("Render cancelled by user")

            except Exception as e:
                self.finished.emit(f"Error rendering chunk {i}: {str(e)}", "")
                return

        #### fusion block ####
        try:
            fused_file = self.output_file

            if len(self.chunk_files) == 1:
                shutil.copy2(self.chunk_files[0], fused_file)
            else:
                combined = builtins.pydub.AudioSegment.empty()
                for file in self.chunk_files:
                    combined += builtins.pydub.AudioSegment.from_wav(file)
                combined.export(fused_file, format="wav")

            self.finished.emit("Fused file created successfully", fused_file)
            print(f"Fused file created successfully: {fused_file}")

        except Exception as e:
            self.finished.emit(f"Error in fusion: {str(e)}", "")
            print(f"Error in fusion: {str(e)}")

    def cleanup_partial_files(self):
        # Clean up files if rendering is cancelled
        for file in self.chunk_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass

    def __del__(self):
        # Ensure proper thread cleanup
        self.wait(500)
        self.terminate()
    
    def cancel(self):
        # Request thread cancellation
        self._is_cancelled = True


def stop_rendering(context):
    if hasattr(context, 'render_thread'):
        context.render_thread.cancel()
        
        
        
        if context.render_thread.isRunning():
            context.render_thread.quit()
            context.render_thread.wait(2000)
        
        del context.render_thread

def render_text(context, text, voice, language, speed, output_file, blend_voice=None, blend_balance=None):
    stop_rendering(context)

    required_instances = {
        "kokoro_instance": True,
        "espeak_instance": True,
        "g2p_instance": language not in ["Japanese", "Mandarin Chinese"],
        "ja_g2p_instance": language == "Japanese",
        "zh_g2p_instance": language == "Mandarin Chinese"
    }
    
    for instance_name, required in required_instances.items():
        if required and not hasattr(builtins, instance_name):
            global_signals.output_signal.emit(f"Error: {instance_name} not loaded yet.")
            return

    if hasattr(context, 'render_thread') and context.render_thread.isRunning():
        context.render_thread.terminate()
        context.render_thread.wait(1000)

    global_signals.toggleGifSignal.emit()
    global_signals.output_signal.emit("Rendering chunks...")
    global_signals.new_render_started.emit()

    temp_folder = os.path.join(os.getcwd(), f"temp_chunks_{uuid.uuid4().hex}")
    os.makedirs(temp_folder, exist_ok=True)
    context.render_thread = RenderChunksThread(
        text=text,
        voice=voice,
        speed=speed,
        language=language,
        kokoro_instance=kokoro_instance,
        is_phonemes=True,
        temp_folder=temp_folder,
        output_file=output_file,
        blend_voice=blend_voice,
        blend_balance=blend_balance
    )

    context.render_thread.chunk_ready.connect(global_signals.addChunkToPlayerSignal.emit)

    # add statusbar text
    
    finished_handler = partial(
        handle_finished, 
        context=context,
        temp_folder=temp_folder
    )

    context.render_thread.finished.connect(finished_handler)

    context.render_thread.start()

def handle_finished(msg, file_path, context, temp_folder):
    global_signals.output_signal.emit(msg)
    global_signals.statusbar_signal.emit(msg)
    global_signals.toggleGifSignal.emit()
    global_signals.stopAnimationSignal.emit()
    
    # Simplify the success check
    success = bool(file_path)
    global_signals.fused_file_completed.emit(success, file_path if success else msg, temp_folder)        
