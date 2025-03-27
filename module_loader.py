# module_loader.py
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtCore import QMetaObject, Q_ARG, Qt

import importlib
import importlib.util
import builtins
import sys
import os
import traceback
import subprocess
import requests
import time
import platform
import zipfile

from signals import global_signals


class ModuleLoaderThread(QThread):
    loaded = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, callback_function=None, message_callback_target=None, progress_callback_target=None, download_callback_target=None, downState_callback_target=None):
        super().__init__()
        self.callback_function = callback_function
        self.message_callback_target = message_callback_target
        self.progress_callback_target = progress_callback_target
        self.download_callback_target = download_callback_target
        self.downState_callback_target = downState_callback_target
        self._stop_requested = False
        self.global_signals = global_signals

    def safe_message(self, msg):
        QMetaObject.invokeMethod(
            self.message_callback_target, "updateMessage",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, msg)
        )

    def safe_loading_progress(self, progress):
        QMetaObject.invokeMethod(
            self.progress_callback_target, "updateProgress",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(int, progress)
        )

    def safe_download_progress(self, download_p):
        QMetaObject.invokeMethod(
            self.download_callback_target, "updateDownload",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(int, download_p)  # Pass the integer parameter
        )

    def safe_download_state(self, down_state):
        QMetaObject.invokeMethod(
            self.downState_callback_target, "toggleDownloadBar",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, down_state)
        )

    def check_and_install_missing_modules(self):
        required_modules = [
            ("soundfile", "Soundfile audio library", None, None),
            ("numpy", "NumPy computing library", None, None),
            ("onnxruntime", "ONNX Runtime", "1.20.1", None),
            ("asyncio", "asyncio module", None, None),
            ("kokoro_onnx", "Kokoro ONNX engine", None, None),
            ("misaki", "Grapheme-to-Phoneme engine", None, None),
            ("jaconv", "jaconv Japanese Converter", None, None),
            ("mojimoji", "mojimoji Japanese Converter", None, None),
            ("ordered_set", "OrderedSet data structure", None, None),
            ("pydub", "Pydub audio processing library", None, None),
            ("pypinyin", "Chinese to pinyin characters convertor", None, None),
            ("cn2an", "Chinese and Arabic numerals convertor", None, None),
            ("jieba", "Chinese text segmentation tool", None, None),
            ("unidic-lite", "unidic-lite package", None, "unidic_lite")


        ]
        ext_pkg_dir = os.path.join(os.path.dirname(sys.executable), "external_packages")
        if os.path.isdir(ext_pkg_dir) and ext_pkg_dir not in sys.path:
            sys.path.insert(0, ext_pkg_dir)
            importlib.invalidate_caches()
            self.safe_message(f"Added {ext_pkg_dir} to sys.path.")

        missing_packages = []
        for pkg_name, desc, version, import_name in required_modules:

            spec = importlib.util.find_spec(import_name or pkg_name)
            if not spec:
                missing_packages.append((pkg_name, version))
        if missing_packages:
            self.safe_message(f"Missing packages detected: {missing_packages}")
            packages_spec = []
            for pkg, ver in missing_packages:
                if ver:
                    packages_spec.append(f"{pkg}=={ver}")
                else:
                    packages_spec.append(pkg)
            
            result = self.external_install_packages(packages_spec)
            if not result:
                self.safe_message("External installation failed for packages: " + ", ".join(packages_spec))
            return result
        return True

    def external_install_packages(self, packages_spec):
        import os, subprocess, sys, importlib, shutil

        # Determine the application's executable directory
        exe_dir = os.path.dirname(sys.executable)
        
        # Create the external_packages directory if it doesn't exist
        ext_pkg_dir = os.path.join(exe_dir, "external_packages")
        os.makedirs(ext_pkg_dir, exist_ok=True)
        
        # Create a log file for debugging
        log_file_path = os.path.join(exe_dir, "pip_install_log.txt")
        self.safe_message(f"Logging pip installation to: {log_file_path}")
        
        with open(log_file_path, "w") as log_file:
            log_file.write(f"Installation started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Target directory: {ext_pkg_dir}\n")
            log_file.write(f"Packages to install: {packages_spec}\n")
            log_file.write(f"Python executable: {sys.executable}\n")
            log_file.write(f"sys.path: {sys.path}\n\n")
        
        # Try to determine the correct Python executable path
        python_exe = sys.executable
        if 'python' not in os.path.basename(python_exe).lower():
            # This might be a frozen executable, try to find Python in the system
            possible_paths = ['python', 'python3', 
                            r'C:\Python312\python.exe',
                            r'C:\Program Files\Python312\python.exe']
            
            for path in possible_paths:
                try:
                    subprocess.run([path, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    python_exe = path
                    self.safe_message(f"Found Python at: {python_exe}")
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
        
        # Try a direct pip installation first
        self.safe_message(f"Attempting direct pip installation to {ext_pkg_dir}")
        
        try:
            packages_str = " ".join(packages_spec)
            pip_cmd = f'"{python_exe}" -m pip install --no-cache-dir --target="{ext_pkg_dir}" {packages_str}'
            self.safe_message(f"Running command: {pip_cmd}")
            
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Running command: {pip_cmd}\n")
            
            # Run pip directly
            process = subprocess.Popen(
                pip_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            with open(log_file_path, "a") as log_file:
                log_file.write(f"STDOUT:\n{stdout}\n\n")
                log_file.write(f"STDERR:\n{stderr}\n\n")
            
            if process.returncode == 0:
                self.safe_message("Direct pip installation succeeded")
                # Check if the directory has content
                dir_content = os.listdir(ext_pkg_dir)
                self.safe_message(f"Directory content: {dir_content}")
                
                if ext_pkg_dir not in sys.path:
                    sys.path.insert(0, ext_pkg_dir)
                importlib.invalidate_caches()
                return True
            else:
                self.safe_message(f"Direct pip installation failed with return code: {process.returncode}")
                self.safe_message(f"Error: {stderr}")
        except Exception as e:
            self.safe_message(f"Error during direct pip installation: {str(e)}")
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Exception during direct installation: {str(e)}\n")
                log_file.write(f"Traceback: {traceback.format_exc()}\n\n")
        
        # If direct installation failed, try the batch file as a fallback
        self.safe_message("Attempting installation via batch file as fallback")
        
        # Determine the path to the installer script
        if getattr(sys, 'frozen', False):
            bat_file = os.path.join(sys._MEIPASS, "install_package.bat")
        else:
            bat_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_package.bat")

        if not os.path.exists(bat_file):
            self.safe_message(f"External installer script not found at: {bat_file}")
            return False
        
        # Create a modified batch file with the correct Python path
        temp_bat_file = os.path.join(exe_dir, "temp_install_package.bat")
        with open(bat_file, "r") as src, open(temp_bat_file, "w") as dst:
            content = src.read()
            # Replace python with the full path
            content = content.replace("python ", f'"{python_exe}" ')
            dst.write(content)
        
        # Build command
        command = [temp_bat_file] + packages_spec
        command_str = " ".join(command)
        self.safe_message(f"Running command: {command_str}")
        
        with open(log_file_path, "a") as log_file:
            log_file.write(f"Running batch command: {command_str}\n")
        
        try:
            # Run the BAT file
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Read stdout line by line
            output_lines = []
            while True:
                line = process.stdout.readline()
                if line:
                    output_line = line.strip()
                    output_lines.append(output_line)
                    self.safe_message(output_line)
                if line == "" and process.poll() is not None:
                    break
            
            # Capture stderr
            stderr = process.stderr.read()
            if stderr:
                self.safe_message("ERROR: " + stderr.strip())
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"STDERR from batch:\n{stderr}\n\n")
            
            retcode = process.poll()
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Batch file returned: {retcode}\n")
                log_file.write(f"Output:\n" + "\n".join(output_lines) + "\n\n")
                
                # Log directory contents
                try:
                    log_file.write(f"External packages directory content:\n")
                    if os.path.exists(ext_pkg_dir):
                        for item in os.listdir(ext_pkg_dir):
                            item_path = os.path.join(ext_pkg_dir, item)
                            if os.path.isdir(item_path):
                                log_file.write(f"  DIR: {item}\n")
                            else:
                                log_file.write(f"  FILE: {item} ({os.path.getsize(item_path)} bytes)\n")
                    else:
                        log_file.write("  Directory does not exist\n")
                except Exception as e:
                    log_file.write(f"Error listing directory: {str(e)}\n")
            
            if retcode == 0:
                # Check if anything was installed
                if os.path.exists(ext_pkg_dir) and os.listdir(ext_pkg_dir):
                    if ext_pkg_dir not in sys.path:
                        sys.path.insert(0, ext_pkg_dir)
                    importlib.invalidate_caches()
                    self.safe_message(f"Successfully installed packages to: {ext_pkg_dir}")
                    return True
                else:
                    self.safe_message(f"WARNING: Installation completed but directory is empty: {ext_pkg_dir}")
                    return False
            else:
                self.safe_message(f"External installer returned error code: {retcode}")
                return False

        except Exception as e:
            self.safe_message(f"Error running external installer: {str(e)}")
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Exception during batch installation: {str(e)}\n")
                log_file.write(f"Traceback: {traceback.format_exc()}\n")
            return False
        
    def run(self):
        try:
            if self._stop_requested:
                return

            self.safe_message("Initializing modules...")

            # First, check and install all missing modules at once.
            if not self.check_and_install_missing_modules():
                raise Exception("Failed to install missing packages externally.")

            # Now, go through your list; these should now be present.
            self._verify_module("soundfile", "Soundfile audio library")
            self._verify_module("numpy", "NumPy computing library")
            self._verify_module("onnxruntime", "ONNX Runtime", version="1.20.1")
            self._verify_module("kokoro_onnx", "Kokoro ONNX engine")
            self._verify_module("misaki", "Grapheme-to-Phoneme engine")
            self._verify_module("jaconv", "jaconv Japanese Converter")
            self._verify_module("mojimoji", "mojimoji Japanese Converter")
            self._verify_module("ordered_set", "OrderedSet data structure")
            self._verify_module("pypinyin", "Chinese to pinyin characters convertor")
            self._verify_module("cn2an", "Chinese and Arabic numerals convertor")
            self._verify_module("jieba", "Chinese text segmentation tool")
            self._verify_module("unidic-lite", "unidic-lite package", import_name="unidic_lite")


            # Verify misaki[ja] and misaki[zh] modules
            self._verify_module("misaki.ja", "Grapheme-to-Phoneme engine for Japanese")
            self._verify_module("misaki.zh", "Grapheme-to-Phoneme engine for Chinese")

            # Set up FFmpeg
            self._verify_ffmpeg()

            self._verify_module("pydub", "Pydub audio processing library")

            self._verify_model_files()
            sf = importlib.import_module("soundfile")
            np = importlib.import_module("numpy")
            pydub = importlib.import_module("pydub")

            # Import espeak and EspeakG2P
            espeak = importlib.import_module("misaki.espeak")
            EspeakG2P = getattr(espeak, "EspeakG2P")

            # Import Japanese and Chinese G2P modules
            ja_g2p_module = importlib.import_module("misaki.ja")
            zh_g2p_module = importlib.import_module("misaki.zh")

            try:
                kokoro_mod = importlib.import_module("kokoro_onnx")
                self.safe_message("Instantiating Kokoro TTS engine ...")
                self.safe_loading_progress(10)
                instance = kokoro_mod.Kokoro("kokoro/kokoro-v1.0.onnx", "kokoro/voices-v1.0.bin")
                self.callback_function(instance)
            except Exception as e:
                full_error = traceback.format_exc()
                with open("detailed_error.log", "w") as f:
                    f.write(full_error)
                self.safe_message(f"Error during Kokoro instance creation: {full_error}")
                raise

            builtins.sf = sf
            builtins.np = np
            builtins.pydub = pydub
            builtins.kokoro_instance = kokoro_mod.Kokoro("kokoro/kokoro-v1.0.onnx", "kokoro/voices-v1.0.bin")
            builtins.espeak_instance = espeak
            builtins.g2p_instance = EspeakG2P


            # Initialize the Japanese G2P converter
            builtins.ja_g2p_instance = ja_g2p_module.JAG2P()

            # Initialize the Chinese G2P converter
            builtins.zh_g2p_instance = zh_g2p_module.ZHG2P()

            self.loaded.emit(builtins.kokoro_instance)
            self.loaded.emit(builtins.espeak_instance)
            self.loaded.emit(builtins.g2p_instance)
            self.loaded.emit(builtins.ja_g2p_instance)
            self.loaded.emit(builtins.zh_g2p_instance)



        except Exception as e:
            full_error = traceback.format_exc()
            with open("error_debug.log", "w") as f:
                f.write(full_error)
            self.safe_message(f"Module initialization failed: {str(e)}\n{full_error}")

    def external_install_package(self, package_name, version=None):
        """Install a single package using the external installer"""
        package_spec = f"{package_name}=={version}" if version else package_name
        return self.external_install_packages([package_spec])

    def _verify_module(self, name, description, version=None, import_name=None):
        self.safe_loading_progress(10)
        self.safe_message(f"Verifying {description}...")
        spec = importlib.util.find_spec(import_name or name)
        if not spec:
            self.safe_message(f"{description} not found. Installing externally...")
            package_spec = f"{name}=={version}" if version else name
            if not self.external_install_packages([package_spec]):  # Use external_install_packages with a list
                raise ImportError(f"Failed to install {name}")
            importlib.invalidate_caches()
            spec = importlib.util.find_spec(import_name or name)
            if not spec:
                raise ImportError(f"{name} module not found in:\n{sys.path}")

        try:
            importlib.import_module(import_name or name)
            self.safe_loading_progress(20)
            self.safe_message(f"Successfully imported {import_name or name}")
        except ImportError as e:
            raise RuntimeError(f"{name} import failed: {str(e)}")


    def _verify_model_files(self):

        self.safe_message("Checking for required model files ...")
        all_success = True

        files = ['kokoro-v1.0.onnx', 'voices-v1.0.bin']
        directory = 'kokoro'
        urls = {
            'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
            'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin'
        }

        if not os.path.exists(directory):
            os.makedirs(directory)

        for file in files:
            if self._stop_requested:
                return
            file_path = os.path.join(directory, file)
            self.safe_message(f'Verifying file: "{file}"')

            if not os.path.exists(file_path):
                self.safe_message(f'"{file}" not found. Starting download...')
                success = self.download_file(urls[file], file_path)
                if not success:
                    all_success = False
            else:
                try:
                    response = requests.head(urls[file], allow_redirects=True)
                    expected_size = int(response.headers.get('content-length', 0))
                    actual_size = os.path.getsize(file_path)
                    if expected_size > 0 and actual_size != expected_size:
                        raise ValueError(f"Existing {file} is incomplete")
                    else:
                        self.safe_loading_progress(20)

                        self.safe_message(f'"{file}" verified: {actual_size} bytes (expected: {expected_size} bytes).')
                        all_success = True
                except Exception:
                    self.safe_message(f'Redownloading corrupted "{file}"')
                    os.remove(file_path)
                    success = self.download_file(urls[file], file_path)
                    if not success:
                        all_success = False


        if all_success:
            self.global_signals.files_ready.emit()
        else:
            self.safe_message("Some files failed to download")
        self.finished.emit()

    def _verify_ffmpeg(self):
        self.safe_message("Setting up FFmpeg...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(script_dir, "ffmpeg")

        # Check if FFmpeg is already set up locally
        if os.path.exists(ffmpeg_dir):
            subdirs = [d for d in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, d))]
            if subdirs:
                bin_dir = os.path.join(ffmpeg_dir, subdirs[0], "bin")
                if os.path.exists(os.path.join(bin_dir, "ffmpeg.exe")):
                    self.safe_message("FFmpeg already found at: " + bin_dir)
                    # Add FFmpeg bin directory to PATH for pydub to find
                    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
                    self.safe_message(f"Added {bin_dir} to PATH")
                    # Verify executables exist
                    ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")
                    ffprobe_path = os.path.join(bin_dir, "ffprobe.exe")
                    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
                        self.safe_message(f"Warning: ffmpeg.exe or ffprobe.exe not found in {bin_dir}")
                        # Optionally raise an error here if FFmpeg is critical
                    else:
                        self.safe_message(f"FFmpeg executables verified in PATH.")
                    return # Exit the function as FFmpeg is set up
                
            
        # Determine FFmpeg URL based on system architecture
        if platform.architecture()[0] == "64bit":
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        else:
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials-32.zip"

        local_zip = os.path.join(script_dir, "ffmpeg.zip")

        # Download FFmpeg
        self.safe_message("Downloading FFmpeg from " + url)
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(local_zip, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_requested:
                        os.remove(local_zip)
                        return
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        self.safe_download_progress(progress)
            self.safe_message("Download complete.")
        except requests.RequestException as e:
            self.safe_message("Failed to download FFmpeg: " + str(e))
            raise

        # Extract the zip file
        self.safe_message("Extracting FFmpeg...")
        try:
            with zipfile.ZipFile(local_zip, "r") as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
        except zipfile.BadZipFile:
            self.safe_message("Downloaded FFmpeg zip file is corrupted")
            raise

        # Find the bin directory
        subdirs = [d for d in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, d))]
        if not subdirs:
            self.safe_message("Failed to find FFmpeg binaries after extraction")
            raise Exception("FFmpeg extraction failed")
        bin_dir = os.path.join(ffmpeg_dir, subdirs[0], "bin")

        # Clean up the zip file
        os.remove(local_zip)
        self.safe_message("FFmpeg setup complete at: " + bin_dir)

        # Add FFmpeg bin directory to PATH for pydub to find
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
        self.safe_message(f"Added {bin_dir} to PATH")
        # Verify executables exist
        ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")
        ffprobe_path = os.path.join(bin_dir, "ffprobe.exe")
        if not os.path.exists(ffmpeg_path) or not os.path.exists(ffprobe_path):
            self.safe_message(f"Warning: ffmpeg.exe or ffprobe.exe not found in {bin_dir}")
            # Optionally raise an error here if FFmpeg is critical
        else:
            self.safe_message(f"FFmpeg executables verified in PATH.")
            
    
    def download_file(self, url, destination, retries=10, backoff_factor=1):
        self.safe_download_progress(0)
        for attempt in range(retries):
            if self._stop_requested:
                return False
            try:
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    self.safe_message(f'Initiating download for "{os.path.basename(destination)}" (expected size: {total_size} bytes)...')

                    if os.path.exists(destination) and total_size > 0:
                        actual_size = os.path.getsize(destination)
                        if actual_size == total_size:
                            self.safe_message(f'"{os.path.basename(destination)}" already exists and is complete.')
                            return True
                        else:
                            self.safe_message(f'"{os.path.basename(destination)}" exists but is incomplete (size: {actual_size}/{total_size} bytes). Redownloading...')

                    last_progress = -1  # initialize to a value that won't match any valid progress
                    with open(destination, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self._stop_requested:
                                os.remove(destination)
                                return False
                            file.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                if progress != last_progress:
                                    self.safe_download_progress(progress)
                                    last_progress = progress

                    if total_size > 0:
                        actual_size = os.path.getsize(destination)
                        if actual_size != total_size:
                            os.remove(destination)
                            raise Exception(f"Size mismatch: {actual_size} vs {total_size} bytes")

                    self.safe_message(f'Download of "{os.path.basename(destination)}" completed.')

                    return True
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    self.safe_message(f'Retrying "{os.path.basename(destination)}" in {wait_time:.1f}s...')
                    time.sleep(wait_time)
                else:
                    self.safe_message(f'Failed to download "{os.path.basename(destination)}": {str(e)}')
                    return False
        return False


def load_heavy_modules(callback_function, message_callback_target, progress_callback_target, download_callback_target, downState_callback_target):
    loader_thread = ModuleLoaderThread(
        callback_function=callback_function,
        message_callback_target = message_callback_target,
        progress_callback_target = progress_callback_target,
        download_callback_target = download_callback_target,
        downState_callback_target = downState_callback_target
    )
    loader_thread.start()
    return loader_thread

