# module_loader.py
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtCore import QMetaObject, Q_ARG, Qt

import importlib
import importlib.util
import builtins
import sys
import os
import re
import traceback
import subprocess
import requests
import time
import platform
import zipfile
import shutil

from core.signals import global_signals

LOADER_ERROR_LOG_FILE = "error_debug.log"

def log_loader_error(message):
    """Helper function to append loader errors to the dedicated log file."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        # Ensure the log directory exists (useful if running from odd places)
        log_dir = os.path.dirname(LOADER_ERROR_LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
             os.makedirs(log_dir, exist_ok=True) # Create dir if it doesn't exist

        # Open in append mode, create if doesn't exist
        with open(LOADER_ERROR_LOG_FILE, "a", encoding='utf-8') as f:
            f.write(f"--- {timestamp} ---\n")
            f.write(f"{message}\n\n")
    except Exception as log_e:
        # Fallback if logging fails
        print(f"CRITICAL: Failed to write to loader error log '{LOADER_ERROR_LOG_FILE}': {log_e}")
        print(f"Original Error Message:\n{message}")

def add_bundled_libs_to_path():
    """Adds the bundled_libs directory to sys.path and the DLL search path."""
    try:
        # Determine base_dir (handle frozen/script mode)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.join(os.path.dirname(sys.executable), '_internal', 'core')
            if not os.path.isdir(base_dir):
                 base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        bundled_libs_path = os.path.join(base_dir, 'bundled_libs')

        # --- Check if bundled_libs directory itself exists ---
        if os.path.isdir(bundled_libs_path):
            added_to_sys_path = False
            if bundled_libs_path not in sys.path:
                sys.path.insert(0, bundled_libs_path)
                print(f"INFO: Added bundled libraries path to sys.path: {bundled_libs_path}")
                importlib.invalidate_caches()
                added_to_sys_path = True
            else:
                print(f"INFO: Bundled libraries path already in sys.path: {bundled_libs_path}")
                added_to_sys_path = True

            dll_path_added = False
            if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
                try:
                    abs_bundled_libs_path = os.path.abspath(bundled_libs_path)
                    print(f"INFO: Attempting to add bundled libs to DLL search path: {abs_bundled_libs_path}")
                    os.add_dll_directory(abs_bundled_libs_path)
                    print(f"INFO: Successfully added bundled libs to DLL search path.")
                    dll_path_added = True
                except OSError as e_dll_os:
                    print(f"WARNING: Failed to add bundled libs path '{abs_bundled_libs_path}' to DLL search path: {e_dll_os}")
                except Exception as e_dll:
                    print(f"WARNING: Unexpected error adding bundled libs path to DLL search path: {e_dll}")
            elif sys.platform != 'win32':
                dll_path_added = True
                print("INFO: Not on Windows, skipping DLL search path addition.")
            else:
                print("WARNING: os.add_dll_directory not available. Bundled DLLs might not be found by dependent libraries.")

            return added_to_sys_path
        else:
            print(f"WARNING: Bundled libraries path not found: {bundled_libs_path}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to configure bundled libs path: {e}")
        print(traceback.format_exc())
        return False


BUNDLED_LIBS_ADDED = add_bundled_libs_to_path()
if not BUNDLED_LIBS_ADDED:
     print("WARNING: Could not set up bundled libraries path. Features requiring bundled libs might fail.")


def get_uv_path():
    """ Finds the appropriate uv executable path whether running bundled or directly."""
    if getattr(sys, 'frozen', False):
        # --- Bundled Mode ---
        # Look for uv.exe bundled by PyInstaller
        try:
            base_path = sys._MEIPASS
            uv_exe = os.path.join(base_path, "uv.exe") # Assumes bundled to root '.'
            if os.path.exists(uv_exe):
                return uv_exe
            else:
                print("WARNING: Running bundled, but bundled uv.exe not found!")
                return None
        except AttributeError:
             print("WARNING: sys._MEIPASS not found, cannot find bundled uv.")
             return None
    else:
        uv_exe_path = shutil.which("uv")
        if uv_exe_path:
            return uv_exe_path
        else:
            print("WARNING: Running directly, uv not found in PATH.")
            return None


class ModuleLoaderThread(QThread):
    loaded = pyqtSignal(object)
    error = pyqtSignal(str)
    set_next_progress_milestone = pyqtSignal(int)

    def _get_app_root(self):
        """Determines the application's root directory."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            core_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.dirname(core_dir)

    def __init__(self, callback_function=None, message_callback_target=None, progress_bar_widget=None, download_callback_target=None, downState_callback_target=None):
        super().__init__()
        self.callback_function = callback_function
        self.message_callback_target = message_callback_target
        # Store the progress bar target itself to call methods on it
        self.progress_bar_widget = progress_bar_widget # Assuming this IS the progress bar widget
        self.download_callback_target = download_callback_target
        self.downState_callback_target = downState_callback_target
        self._stop_requested = False
        self.global_signals = global_signals
        self.loading_successful = False
        self._current_progress_target = 0.0 # Use float internally now




    def safe_message(self, msg):
        # Prepend timestamp with milliseconds
        timestamp = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        log_msg = f"[{timestamp}] {msg}" # Add timestamp to the message

        if self.message_callback_target:
            QMetaObject.invokeMethod(
                self.message_callback_target, "updateMessage",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, log_msg) # Send the timestamped message
            )
        else:
            print(f"LoaderThread Msg: {log_msg}") # Fallback print with timestamp

    def safe_loading_progress(self, progress: float):
        # Clamp progress to 0-100 range
        clamped_progress_float = max(0.0, min(progress, 100.0))
        self._current_progress_target = clamped_progress_float

        # The progress bar widget expects an integer for its value animation endpoint
        progress_int = int(clamped_progress_float)

        # Use the stored progress bar widget reference
        if self.progress_bar_widget:
            # Use invokeMethod to call setValueAnimated on the GUI thread
            QMetaObject.invokeMethod(
                self.progress_bar_widget, "setValueAnimated",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(float, clamped_progress_float) # Pass the float target
            )
        else:
             print(f"LoaderThread Progress: {clamped_progress_float:.1f}%") # Fallback

    def signal_next_milestone(self, percentage: int):
        # print(f"Signaling next milestone: {percentage}%") # Debug
        self.set_next_progress_milestone.emit(percentage)


    def safe_download_progress(self, download_p):
        if self.download_callback_target:
            QMetaObject.invokeMethod(
                self.download_callback_target, "updateDownload",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, download_p)
            )

    def check_and_install_missing_modules(self):
        required_modules = [
            ("soundfile", "Soundfile audio library", None, None),
            ("ordered_set", "OrderedSet data structure", None, None),
            ("numpy", "NumPy computing library", None, None),
            ("torch", "Torch", "2.5", None),
            ("torchaudio", "Torch Audio", "2.5", None), 
            ("onnxruntime", "ONNX Runtime", "1.20.1", None),
            ("kokoro_onnx", "Kokoro ONNX engine", None, None),
            ("fugashi", "Japanese tokenizer", None, None),
            ("misaki", "Grapheme-to-Phoneme engine", None, None),
            ("jaconv", "jaconv Japanese Converter", None, None),
            ("mojimoji", "mojimoji Japanese Converter", None, None),
            ("pypinyin", "Chinese to pinyin characters convertor", None, None),
            ("cn2an", "Chinese and Arabic numerals convertor", None, None),
            ("jieba", "Chinese text segmentation tool", None, None),
            ("unidic-lite", "unidic-lite package", None, "unidic_lite")
        ]

        # Determine external packages directory path
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            ext_pkg_dir = os.path.join(base_dir, "external_packages")
        else:
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ext_pkg_dir = os.path.join(project_root, "external_packages")
                self.safe_message(f"Project root detected: {project_root}")
            except Exception as e_path:
                self.safe_message(f"Error calculating project root: {e_path}. Falling back to executable's directory.")
                base_dir = os.path.dirname(sys.executable)
                ext_pkg_dir = os.path.join(base_dir, "external_packages")

        self.safe_message(f"Using external packages directory: {ext_pkg_dir}")

        # --- Add external_packages to sys.path ---
        if os.path.isdir(ext_pkg_dir) and ext_pkg_dir not in sys.path:
            sys.path.insert(0, ext_pkg_dir)
            importlib.invalidate_caches()
            self.safe_message(f"Added existing {ext_pkg_dir} to sys.path for checks.")
        elif not os.path.isdir(ext_pkg_dir):
            self.safe_message(f"External packages directory {ext_pkg_dir} does not exist yet.")

        missing_packages = []
        self.safe_message("Checking required modules...")
        for pkg_name, desc, version, import_name in required_modules:
            check_name = import_name or pkg_name
            self.safe_message(f"Checking for: {check_name} ({desc})")
            try:
                spec = importlib.util.find_spec(check_name)
                if spec:
                    if version:
                        try:
                            # Temporarily add path for import check if needed
                            needs_path_add = ext_pkg_dir not in sys.path and os.path.isdir(ext_pkg_dir)
                            if needs_path_add:
                                sys.path.insert(0, ext_pkg_dir)
                                importlib.invalidate_caches()

                            mod = importlib.import_module(check_name)
                            installed_version = getattr(mod, '__version__', None)

                            if needs_path_add: # Clean up path if added
                                sys.path.pop(0)
                                importlib.invalidate_caches()


                            if installed_version:
                                self.safe_message(f"Found {check_name} version {installed_version}")
                                if installed_version != version:
                                    self.safe_message(f"Version mismatch for {check_name}. Found {installed_version}, require {version}. Will reinstall.")
                                    missing_packages.append((pkg_name, version))
                                else:
                                    self.safe_message(f"Version {version} matches.")
                            else:
                                self.safe_message(f"Found {check_name}, but couldn't determine version.")
                        except Exception as e:
                            self.safe_message(f"Found {check_name}, but failed to import/check version: {e}")
                            # If version check fails, maybe assume mismatch?
                            missing_packages.append((pkg_name, version))
                    else:
                        self.safe_message(f"Found {check_name}.")
                else:
                    self.safe_message(f"{check_name} not found.")
                    missing_packages.append((pkg_name, version))
            except ModuleNotFoundError:
                self.safe_message(f"{check_name} not found (ModuleNotFoundError).")
                missing_packages.append((pkg_name, version))
            except Exception as e:
                self.safe_message(f"Error checking for {check_name}: {e}")
                missing_packages.append((pkg_name, version))

        if missing_packages:
            self.safe_message(f"Missing or mismatched packages detected: {missing_packages}")
            packages_spec = []
            for pkg, ver in missing_packages:
                 if ver: packages_spec.append(f"{pkg}=={ver}")
                 else: packages_spec.append(pkg)

            self.safe_message(f"Calling external_install_packages for: {packages_spec}")

            self.signal_next_milestone(50)

            result = self.external_install_packages(packages_spec, ext_pkg_dir)
            self.safe_message(f"external_install_packages returned: {result}")

            if result:
                self.safe_loading_progress(50.0)
                self.safe_message("Installation reported success. Proceeding with path/cache update.")
                if ext_pkg_dir not in sys.path:
                    self.safe_message(f"Attempting to add {ext_pkg_dir} to sys.path...")
                    sys.path.insert(0, ext_pkg_dir)
                    self.safe_message(f"Successfully added {ext_pkg_dir} to sys.path.")
                else:
                    self.safe_message(f"{ext_pkg_dir} was already in sys.path.")

                self.safe_message("Attempting to invalidate import caches...")
                importlib.invalidate_caches()
                self.safe_message("Successfully invalidated import caches.")
                self.safe_message("External installation successful. Module checks complete.")
                return True
            else:
                self.safe_loading_progress(50.0)
                self.safe_message("External installation failed for packages: " + ", ".join(packages_spec))
                return False
        else:
            self.safe_message("All required packages seem to be present and versions match.")
            self.safe_loading_progress(50.0)
            return True

    def external_install_packages(self, packages_spec, ext_pkg_dir):
        """Installs packages using uv, attempting to provide progress feedback."""
        self.safe_message(f"Attempting package installation using uv: {packages_spec}")
        uv_exe = get_uv_path()
        if not uv_exe:
            self.safe_message("ERROR: Could not locate uv executable.")
            return False
        self.safe_message(f"Using uv executable at: {uv_exe}")

        try:
            os.makedirs(ext_pkg_dir, exist_ok=True)
        except OSError as e:
            self.safe_message(f"ERROR creating directory {ext_pkg_dir}: {e}")
            return False

        if getattr(sys, 'frozen', False):
            log_dir = os.path.dirname(sys.executable)
        else:
            log_dir = self._get_app_root()
            if not os.path.isdir(log_dir): log_dir = os.path.dirname(sys.executable)
        log_file_path = os.path.join(log_dir, "uv_install_log.txt")
        self.safe_message(f"Logging uv installation to: {log_file_path}")

        cmd = [uv_exe, "pip", "install", "--target", ext_pkg_dir, "--no-cache", "-v"]
        cmd.extend(packages_spec)
        self.safe_message(f"Running command: {' '.join(cmd)}")

        try:
            with open(log_file_path, "w", encoding='utf-8') as log_file:
                # ... (log file header writing) ...
                log_file.write(f"Install started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"Target: {ext_pkg_dir}\nPackages: {packages_spec}\n")
                log_file.write(f"uv: {uv_exe}\nCommand: {' '.join(cmd)}\n\n")
                log_file.flush()


                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding='utf-8', errors='replace', bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                full_output = []

                uv_step_count = 0
                # Start progress at the beginning of the uv phase

                while True:
                    if self._stop_requested:
                         process.terminate()
                         self.safe_message("Installation stopped by request.")
                         return False
                    line = process.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line:
                        full_output.append(line)

                process.wait()
                retcode = process.returncode

                log_file.write("\n--- Captured Output ---\n")
                log_file.write("\n".join(full_output))
                log_file.write(f"\n\nReturn code: {retcode}\n")
                log_file.flush()

            if retcode == 0:
                self.safe_message(f"uv process completed successfully.")
                self.safe_message(f"Package installation phase complete (progress at {self._current_progress_target}%).")
                return True
            else:
                self.safe_message(f"uv installation failed (code: {retcode}). Check {log_file_path}.")
                return False
            
        except FileNotFoundError:
            # Define specific error message here
            fnf_error_message = f"Error: uv executable '{uv_exe}' not found."
            self.safe_message(fnf_error_message)
            log_loader_error(fnf_error_message) # Log this specific error
            return False
        except Exception as e:
            # Define specific error message here
            uv_run_error_message = f"Error running uv install: {e}\n{traceback.format_exc()}"
            self.safe_message(f"Error running uv install: {e}") # Keep summary message short
            log_loader_error(uv_run_error_message) # Log detailed error
            return False

    def run(self):
        uv_exe = None
        install_pkgs_error_msg = None

        # Define where the install step progress should end
        # install_steps_start = 55 # Matches uv_process_max in external_install_packages

        try:
            self.safe_message("--- Starting Module Loader Thread ---")
            self._current_progress_target = 0.0 
            self.safe_loading_progress(0)

            self.safe_message("Locating uv executable...")
            uv_exe = get_uv_path()
            if not uv_exe:
                uv_not_found_msg = "ERROR: Could not locate uv executable.\nPlease ensure 'uv' is installed and accessible in the system PATH, or bundled correctly.\nThe application cannot continue."
                log_loader_error(uv_not_found_msg)
                self.safe_message(uv_not_found_msg)
                self.error.emit("uv executable not found.")
                return
            self.safe_message(f"Using uv executable at: {uv_exe}")

            # Optional: Log sys.path info
            # self.safe_message(f"Current sys.path[0]: {sys.path[0] if sys.path else 'Empty'}")

            if self._stop_requested:
                self.safe_message("Stop requested early.")
                return

            self.safe_message("Initializing modules...")
            self.safe_loading_progress(5.0)
            self.signal_next_milestone(45) # Next major step is end of install (60%)
            self.safe_message("Checking/installing required packages...")

            # --- Call check_and_install ---
            install_success = self.check_and_install_missing_modules()

            if not install_success:
                install_pkgs_error_msg = "Package check/installation failed. Cannot proceed."
                log_loader_error(install_pkgs_error_msg + "\nCheck uv_install_log.txt for details.")
                self.safe_message(install_pkgs_error_msg)
                self.error.emit("Failed to install required packages.")
                return

            # --- If install successful, proceed ---
            self.safe_message("Package check/install process complete.")

            # --- Add external_packages to DLL search path ---
            try:
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                    ext_pkg_dir = os.path.join(base_dir, "external_packages")
                else:
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    ext_pkg_dir = os.path.join(project_root, "external_packages")

                if os.path.isdir(ext_pkg_dir):
                    if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
                        try:
                            abs_ext_pkg_path = os.path.abspath(ext_pkg_dir)
                            self.safe_message(f"Attempting to add external packages dir to DLL search path: {abs_ext_pkg_path}")
                            os.add_dll_directory(abs_ext_pkg_path)
                            self.safe_message(f"Successfully added external packages dir to DLL search path.")
                        except OSError as e_dll_os_ext:
                            self.safe_message(f"WARNING: Failed to add external packages path '{abs_ext_pkg_path}' to DLL search path: {e_dll_os_ext}")
                        except Exception as e_dll_ext:
                            self.safe_message(f"WARNING: Unexpected error adding external packages path to DLL search path: {e_dll_ext}")
                else:
                    self.safe_message(f"WARNING: External packages directory {ext_pkg_dir} not found after install, cannot add to DLL path.")
            except Exception as e_add_ext_path:
                 self.safe_message(f"ERROR: Failed during setup of external packages DLL path: {e_add_ext_path}\n{traceback.format_exc()}")


            try:

                self.safe_message("Verifying model files...")
                self.signal_next_milestone(45)
                self._verify_model_files() # Contains download logic which might take time if downloading
                self.safe_loading_progress(45.0)
                self.safe_message("Model file verification complete.")

                self.safe_message("Invalidating import caches (pre-import)...")
                importlib.invalidate_caches()

                self.safe_message("Importing core modules...")

                self.safe_message("Importing soundfile & numpy...")
                self.signal_next_milestone(55)
                sf = importlib.import_module("soundfile")
                np = importlib.import_module("numpy")
                self.safe_loading_progress(55.0)

                self.safe_message("Importing torch ...")
                self.signal_next_milestone(70)
                torch_mod = importlib.import_module("torch")
                try:
                    torch_lib_path = os.path.join(os.path.dirname(torch_mod.__file__), 'lib')
                    if os.path.isdir(torch_lib_path) and hasattr(os, 'add_dll_directory'):
                        os.add_dll_directory(torch_lib_path)
                except Exception as dll_e:
                    self.safe_message(f"ERROR attempting to add torch lib path: {dll_e}")
                self.safe_loading_progress(70.0)

                self.safe_message("Importing torchaudio...")
                self.signal_next_milestone(80)
                torchaudio_mod = importlib.import_module("torchaudio")
                self.safe_loading_progress(80.0)

                self.safe_message("Importing misaki, G2P, jtalk, kokoro...")
                self.signal_next_milestone(85)
                espeak = importlib.import_module("misaki.espeak")
                EspeakG2P = getattr(espeak, "EspeakG2P")
                ja_g2p_module = importlib.import_module("misaki.ja")
                zh_g2p_module = importlib.import_module("misaki.zh")
                pyopenjtalk_mod = importlib.import_module("pyopenjtalk")
                if 'bundled_libs' not in pyopenjtalk_mod.__file__:
                    self.safe_message("WARNING: Imported pyopenjtalk may not be the bundled version!")
                kokoro_mod = importlib.import_module("kokoro_onnx")
                self.safe_loading_progress(85.0)

                self.safe_message("Modules imported successfully.")


                self.safe_message("Instantiating Kokoro TTS engine...")
                self.signal_next_milestone(95)
                app_root = self._get_app_root()
                model_dir = os.path.join(app_root, 'models', 'kokoro')
                kokoro_model_path = os.path.join(model_dir, 'kokoro-v1.0.onnx')
                voices_path = os.path.join(model_dir, 'voices-v1.0.bin')
                if not os.path.exists(kokoro_model_path): raise FileNotFoundError(f"Kokoro model not found: {kokoro_model_path}")
                if not os.path.exists(voices_path): raise FileNotFoundError(f"Voices file not found: {voices_path}")
                instance = kokoro_mod.Kokoro(kokoro_model_path, voices_path)
                self.safe_message("Kokoro instance created.")
                self.safe_loading_progress(95.0)

                self.safe_message("Assigning modules to builtins...")
                self.signal_next_milestone(100)
                builtins.sf = sf
                builtins.np = np
                builtins.torch = torch_mod
                builtins.torchaudio = torchaudio_mod
                builtins.kokoro_instance = instance
                builtins.espeak_instance = espeak
                builtins.g2p_instance = EspeakG2P

                self.safe_message("Instantiating G2P converters...") # Quick, included in Kokoro step time
                builtins.ja_g2p_instance = ja_g2p_module.JAG2P()
                builtins.zh_g2p_instance = zh_g2p_module.ZHG2P()
                self.safe_message("G2P converters instantiated.")

                self.safe_loading_progress(100.0)
                self.safe_message("Calling success callback...")
                if self.callback_function:
                    self.callback_function(builtins.kokoro_instance)
                else:
                    self.safe_message("WARNING: No callback_function set.")

                self.safe_message("--- Module Loader Thread Finished Successfully ---")
                self.loading_successful = True

            except ImportError as e_import:
                import_error_msg = f"ERROR during module import: {str(e_import)}\n{traceback.format_exc()}"
                log_loader_error(import_error_msg)
                self.safe_message(f"ERROR during module import: {str(e_import)}")
                self.error.emit(f"Import failed: {str(e_import)}")
                # Ensure progress reaches end even on error to avoid hanging bar
                self.safe_loading_progress(100.0)
            except Exception as e_inst:
                instantiation_error_msg = f"ERROR during setup/instantiation: {str(e_inst)}\n{traceback.format_exc()}"
                log_loader_error(instantiation_error_msg)
                self.safe_message(f"ERROR during setup/instantiation: {str(e_inst)}")
                self.error.emit(f"Initialization failed: {str(e_inst)}")
                # Ensure progress reaches end even on error
                self.safe_loading_progress(100.0)

        except Exception as e_outer:
            outer_error_summary = f"Module initialization failed (outer scope): {str(e_outer)}"
            outer_error_details = f"{outer_error_summary}\n{traceback.format_exc()}"
            log_loader_error(outer_error_details)
            self.safe_message(outer_error_summary)
            self.error.emit(outer_error_summary)
            # Ensure progress reaches end even on error
            self.safe_loading_progress(100.0)

        finally:
            self.safe_message("--- Module Loader Thread run() method exiting ---")
            if self.loading_successful:
                self.safe_message("Exit status: Success")
            else:
                self.safe_message("Exit status: Failure or Incomplete")

    def _verify_model_files(self):
        self.safe_message("Checking for required model files...")
        all_success = True

        app_root = self._get_app_root()
        models_base_dir = os.path.join(app_root, 'models')
        directory = os.path.join(models_base_dir, 'kokoro')

        self.safe_message(f"Looking for models in: {directory}")


        files = ['kokoro-v1.0.onnx', 'voices-v1.0.bin']
        urls = {
            'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
            'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin'
        }

        if not os.path.exists(directory):
             self.safe_message(f"Creating model directory: {directory}")
             try:
                 os.makedirs(directory, exist_ok=True) 
             except OSError as e:
                  self.safe_message(f"ERROR: Failed to create model directory {directory}: {e}")
                  self.error.emit(f"Failed to create model directory: {e}")
                  return


        for file in files:
            if self._stop_requested:
                self.safe_message("Model check stopped by request.")
                return

            file_path = os.path.join(directory, file)
            self.safe_message(f'Verifying file: "{file_path}"')

            if not os.path.exists(file_path):
                self.safe_message(f'"{file}" not found. Starting download...')
                success = self.download_file(urls[file], file_path)
                if not success:
                    self.safe_message(f'Download failed for "{file}".')
                    all_success = False
                else:
                     self.safe_message(f'Download successful for "{file}".')
            else:
                self.safe_message(f'"{file}" found locally. Verifying size...')
                try:
                    response = requests.head(urls[file], allow_redirects=True, timeout=10)
                    response.raise_for_status()
                    expected_size = int(response.headers.get('content-length', -1))
                    actual_size = os.path.getsize(file_path)

                    if expected_size > 0:
                        if actual_size == expected_size:
                            self.safe_message(f'"{file}" size verified: {actual_size} bytes.')
                        else:
                            self.safe_message(f'"{file}" size mismatch! Expected {expected_size}, got {actual_size}. Redownloading...')
                            try: os.remove(file_path)
                            except OSError as e: self.safe_message(f"Warning: Could not remove existing file {file_path}: {e}")
                            success = self.download_file(urls[file], file_path)
                            if not success:
                                self.safe_message(f'Redownload failed for "{file}".')
                                all_success = False
                            else:
                                 self.safe_message(f'Redownload successful for "{file}".')
                    else:
                        self.safe_message(f'Could not verify size for "{file}" (content-length header missing). Assuming OK.')

                except requests.RequestException as e:
                    self.safe_message(f'Error checking remote size for "{file}": {e}. Skipping size check.')
                except Exception as e:
                    self.safe_message(f'Error verifying "{file}": {e}. Attempting redownload...')
                    try: os.remove(file_path)
                    except OSError as e_rem: self.safe_message(f"Warning: Could not remove existing file {file_path}: {e_rem}")
                    success = self.download_file(urls[file], file_path)
                    if not success:
                        self.safe_message(f'Redownload failed for "{file}".')
                        all_success = False
                    else:
                         self.safe_message(f'Redownload successful for "{file}".')

        if all_success:
            self.safe_message("All required model files verified successfully.")
            self.global_signals.files_ready.emit()
        else:
            self.safe_message("ERROR: Some required model files could not be downloaded or verified.")
            self.error.emit("Failed to obtain necessary model files.")


    def download_file(self, url, destination, retries=10, backoff_factor=1):
        self.safe_download_progress(0)
        for attempt in range(retries):
            if self._stop_requested: return False
            try:
                with requests.get(url, stream=True, timeout=30) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    self.safe_message(f'Initiating download for "{os.path.basename(destination)}" (expected size: {total_size} bytes)...')


                    last_progress = -1
                    with open(destination, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self._stop_requested:
                                try: os.remove(destination)
                                except OSError: pass
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
                            try: os.remove(destination)
                            except OSError: pass
                            raise IOError(f"Size mismatch: {actual_size} vs {total_size} bytes")

                    self.safe_message(f'Download of "{os.path.basename(destination)}" completed.')
                    self.safe_download_progress(100)

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


def load_heavy_modules(callback_function, message_callback_target, progress_bar_widget, download_callback_target, downState_callback_target):
    """Creates and returns the ModuleLoaderThread instance."""
    loader_thread = ModuleLoaderThread(
        callback_function=callback_function,
        message_callback_target=message_callback_target,
        progress_bar_widget=progress_bar_widget,
        download_callback_target=download_callback_target,
        downState_callback_target=downState_callback_target
    )
    # Connection of signals is handled in SplashWindow where the thread is started
    return loader_thread