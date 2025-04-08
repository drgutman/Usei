# tts_render.py
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import os
import builtins
import shutil
import re
from functools import partial
import traceback
import time
import uuid

from core.signals import global_signals
from core.utils import settings_manager, split_text_into_chunks


RENDER_LOG_FILE = "render_error.log"


def log_render_error(message):
    """Helper function to append errors to the log file."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(RENDER_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(f"{timestamp} - {message}\n")
    except Exception as log_e:
        print(f"Failed to write to render log: {log_e}") # Fallback print


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
        total_chunks = len(chunks)
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
            if self._is_cancelled: # Check cancellation at the start of the loop
                self.cleanup_partial_files()
                self.finished.emit("Render cancelled by user.", "")
                log_render_error("Render cancelled by user during chunk processing.")
                return

            # --- Emit progress to status bar ---
            global_signals.statusbar_signal.emit(f"Rendering chunk {i + 1} of {total_chunks}...")
            global_signals.output_signal.emit(f"Rendering chunk {i + 1} of {total_chunks}...")
            # ---
            try:
                # ... (rest of the G2P and phoneme logic remains the same) ...
                if self.language in ('American English', 'British English'):
                    phonemes = chunk
                    is_phonemes = False
                elif language_code == 'ja':
                    if re.search(r'[\u3040-\u30FF\u4E00-\u9FFF]', chunk):
                        g2p = builtins.ja_g2p_instance
                        result = g2p(chunk)
                        phonemes = result[0] if isinstance(result, tuple) else result
                        is_phonemes = True
                        if not phonemes:
                            error_msg = f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence for chunk: {chunk[:50]}..."
                            log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
                            self.finished.emit(error_msg, "")
                            global_signals.output_signal.emit(error_msg)
                            return
                    else:
                        phonemes = chunk
                        is_phonemes = False
                elif language_code == 'zh':
                    g2p = builtins.zh_g2p_instance
                    phonemes, _ = g2p(chunk)
                    if not phonemes:
                        error_msg = f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence for chunk: {chunk[:50]}..."
                        log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
                        self.finished.emit(error_msg, "")
                        return
                    is_phonemes = True
                else:
                    g2p = builtins.g2p_instance(language=language_code)
                    phonemes, _ = g2p(chunk)
                    if not phonemes:
                        error_msg = f"Error rendering chunk {i}: G2P conversion returned empty phoneme sequence for chunk: {chunk[:50]}..."
                        log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
                        self.finished.emit(error_msg, "")
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
                # Optional: Keep this specific status bar message if desired
                # global_signals.statusbar_signal.emit(f"Temporary file chunk_{i:03d}.wav finished")

                # --- Removed redundant cancellation check here ---

            except Exception as e:
                # --- Log error before emitting finished signal ---
                error_msg = f"Error rendering chunk {i} ({chunk[:30]}...): {str(e)}"
                log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
                # ---
                self.finished.emit(error_msg, "")
                return

        # --- Check cancellation *before* fusion ---
        if self._is_cancelled:
            self.cleanup_partial_files()
            self.finished.emit("Render cancelled by user.", "")
            log_render_error("Render cancelled by user before fusion.")
            return
        # ---

        #### fusion block ####
        global_signals.statusbar_signal.emit("Fusing audio chunks...")
        global_signals.output_signal.emit("Fusing audio chunks...")

        try:
            fused_file = self.output_file

            if not self.chunk_files:
                # Handle case where no chunks were generated (maybe all errors?)
                error_msg = "Error in fusion: No audio chunks were successfully generated."
                log_render_error(error_msg)
                self.finished.emit(error_msg, "")
                return

            if len(self.chunk_files) == 1:
                # If only one chunk, just copy it
                global_signals.output_signal.emit(f"Only one chunk generated, copying directly to {fused_file}")
                shutil.copy2(self.chunk_files[0], fused_file)
            else:
                # Combine multiple chunks
                global_signals.output_signal.emit(f"Fusing {len(self.chunk_files)} chunks using torchaudio...")
                all_waveforms = []
                first_sample_rate = None

                for i, file in enumerate(self.chunk_files):
                    if self._is_cancelled: # Check cancellation during fusion loop
                        self.cleanup_partial_files()
                        self.finished.emit("Render cancelled by user.", "")
                        log_render_error("Render cancelled by user during fusion.")
                        return

                    try:
                        # Load waveform tensor and sample rate
                        waveform, sr = builtins.torchaudio.load(file)

                        if first_sample_rate is None:
                            first_sample_rate = sr
                        elif sr != first_sample_rate:
                            # This shouldn't happen if kokoro is consistent, but good to check
                            error_msg = f"Error: Sample rate mismatch in chunk {i} ({file}). Expected {first_sample_rate}, got {sr}."
                            log_render_error(error_msg)
                            self.finished.emit(error_msg, "")
                            return # Stop fusion on error

                        all_waveforms.append(waveform)
                        global_signals.output_signal.emit(f"Loaded chunk {i+1}/{len(self.chunk_files)} ({file})") # Optional progress

                    except Exception as load_e:
                        error_msg = f"Error loading chunk {file} for fusion: {str(load_e)}"
                        log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
                        self.finished.emit(error_msg, "")
                        return # Stop fusion on error

                # Concatenate along the time/frame dimension (dim=1 for [channels, frames])
                combined_waveform = builtins.torch.cat(all_waveforms, dim=1)
                global_signals.output_signal.emit(f"Concatenated waveforms. Saving to {fused_file} with sample rate {first_sample_rate}...")

                # Save the combined waveform
                builtins.torchaudio.save(fused_file, combined_waveform, first_sample_rate)

            # Signal success
            success_msg = f"Fused file created successfully: {fused_file}"
            global_signals.output_signal.emit(success_msg) # Log success message
            self.finished.emit(success_msg, fused_file) # Emit success signal

        except Exception as e:
            # Log fusion error
            error_msg = f"Error in torchaudio fusion: {str(e)}"
            log_render_error(error_msg + f"\nTraceback:\n{traceback.format_exc()}")
            self.finished.emit(error_msg, "") # Emit failure signal
            # print(error_msg) # Keep console print if desired

    def cleanup_partial_files(self):
        # Clean up files if rendering is cancelled or fails
        log_render_error(f"Cleaning up partial files in {self.temp_folder}")
        for file in self.chunk_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                log_render_error(f"Error removing temp file {file}: {e}")
                pass # Continue cleanup even if one file fails

    def __del__(self):
        # Ensure proper thread cleanup
        self.wait(500)
        # self.terminate() # Avoid terminate if possible

    def cancel(self):
        # Request thread cancellation
        global_signals.output_signal.emit("Render thread cancellation requested.") # Debug print
        self._is_cancelled = True


def stop_rendering(context):
    if hasattr(context, 'render_thread') and context.render_thread: # Check if thread exists
        render_thread = context.render_thread # Get a local reference

        if render_thread.isRunning():
            global_signals.output_signal.emit("Attempting to stop rendering thread...") # Debug print
            render_thread.cancel()  # 1. Signal the thread to stop its work
            render_thread.quit()    # 2. Ask event loop to exit (optional but safe)
            finished = render_thread.wait(2000) # 3. Wait up to 2 seconds for it to finish
            if not finished:
                global_signals.output_signal.emit("Warning: Rendering thread did not finish gracefully within timeout.")
                # Optionally add terminate() here if absolutely necessary, but it's risky
                # render_thread.terminate()
                # render_thread.wait() # Wait after terminate
            else:
                global_signals.output_signal.emit("Rendering thread finished gracefully.")
        else:
             global_signals.output_signal.emit("Rendering thread was not running.")

        # 4. Clean up the reference regardless of whether it was running or finished cleanly
        try:
            del context.render_thread
            global_signals.output_signal.emit("Deleted context.render_thread reference.")
        except AttributeError:
             global_signals.output_signal.emit("context.render_thread already deleted or attribute missing.")
    # else:
    #     global_signals.output_signal.emit("No render_thread found on context to stop.")

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
