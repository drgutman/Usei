# USEI TTS
有声 - adjective - voiced

---

![USEI TTS Logo](https://github.com/drgutman/Usei/blob/main/ui/res/banner.gif)

## USEI TTS is a PyQt6 interface based on the [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx).

  After much effort and bug-fixing, it's finally ready for release!<br>
  (so many bugs, soooo many. I understand now why most open source projects are CLI based)<br>

<a href="https://github.com/drgutman/Usei/blob/main/ui/res/screenshot.png?raw=true" target="_blank">
  <img src="https://github.com/drgutman/Usei/blob/main/ui/res/screenshot.png?raw=true" alt="Screenshot" width="450"/>
</a>

## Features

- **User-Friendly Interface**:
  Easy to use, even for non-technical users.<br>
  With dark and light modes.

- **Fast Rendering**: 
  It is fast, very fast even if it only works on the CPU (GPU support coming soon)
  
- **Languages**:
  - American and British English
  - Japanese
  - French
  - Spanish
  - Italian
  - Hindi
  - Brazilian Portuguese
  - Mandarin Chinese 
  
  each with several voices, male and female.

- **Handles Long Texts**:
  Breaks long texts into chunks and allows on-the-fly playback.
  
- **No-Multi Platform Support, Yet**:
  Unfortunately, it is currently available for Windows (I don't have an Apple computer to build and test it). 

## Installation

  The first time you're going to run the program, it will take some time to install some bigger packages (numpy, torch) that I didn't want to include in the installer, and to download the model files, but after that, it should load pretty quickly.

### Windows
#### WARNING 
  - It will probably be flagged by the Windows Defender or any antivirus that you have. That happens because it doesn't have an official signature registered. I don't have the money to pay for it (it's like 500$ a year, ridiculous) 
  - You might need to run it in admin mode (don't know why this happens)

#### Installer

1. Download the latest version from [[link](https://github.com/drgutman/Usei/releases/download/v1.1.0/Usei_Setup.exe)].
2. Follow the installation prompts.
3. Ensure Python 3.11.9 is installed and added to your PATH.
4. Enjoy!

#### Portable Executable

1. Download the zip file from [[link](https://github.com/drgutman/Usei/releases/download/v1.1.0/usei-portable.zip)].
2. Ensure Python 3.11.9 is installed before running the application.
3. Unpack it in a folder and run the executable.

#### As a Python Script

1. **Requirements**:
   - Python 3.11.9 (ensure "Add Python to PATH" is checked during installation).

2. **Steps**:
   - Download the zip file:
     ```
     https://github.com/drgutman/Usei/archive/refs/heads/main.zip
     ```
     or clone the repository:
     ```
     gh repo clone drgutman/Usei
     ```
   - Create a virtual environment inside the `Usei` folder:
     ```
     python -m venv .venv
     ```
   - Activate the virtual environment:
     ```
     .venv\Scripts\activate
     ```
   - Install the required packages:
     ```
     pip install -r requirements.txt
     ```
   - Run the program:
     ```
     python main.py
     ```

## Change log:
### v1.0.0
  First release

### v1.1.0
  #### Interface:
  - Improved loading bar animation in the splash screen (added background animation too). There's still a small inconsistency that makes it go to 100% and then back to 98% or something but I can't figure it out for the life of me.             
  - There was a small window/widget flickering into existence for a millisecond before the user clicks for the first time on the Replace button in the toolbar.
  - Fixed the statusbar label not showing the text entirely. 
  - Added a new SizeGrip because the default one wasn't visible. It was there and it was working, but you couldn't see it.
                (yes, I had to make a custom drawn size grip with tilted gradients, it's ridiculous how many quirks you find once you start digging)
  - Made the splashscreen log widget taller.

  #### Features/Bug fixes:
  - Added python check at runtime so it doesn't crash the system anymore.
  - Rolled back to python 3.11.9 for compatibility with torch
  - Use UV for package management.
  - Reorganized the folder structure.
  - Streamlined the code and added better error logging and reporting during startup.
  - Moved fugashi from requirements.txt to the module_loader function.
  - Included pyopenjtalk to the source code bundled_libs along with several dlls so the user doesn't have to install cmake or vs_BuildTools to run the program.
            Changed the debug switch in settings to "show console tab" and added a toolbar icon for show console.
                (there's still a small bug when you move the audio player from the bottom dock to the right bottom dock, in which the height is wrong,
                but I couldn't find a way to fix it no matter what I tried)
  - Modified the package check to only delete and reinstall the missing packages or those with the wrong version.


## Next Steps

- [ ] Find and fix any remaining bugs
- [ ] waveform/spectrogram seekbar
- [ ] Add support for more text filetypes
- [ ] Add streaming support
- [ ] Integrate podcast functionality

☒ Implement GPU/CPU switching. no. Just NO! ... I bashed my head on this for 3 or 4 days and I couldn't make it work. It has something to do with onnxruntime versions and their compatibility with the python version, and then you need vs_code build tools, and so on, and so on, and it still crashes, so I'd rather not. It's fast enough on CPU alone.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please open an issue or start a discussion or join us on [Discord](https://discord.gg/x4s4Wznt)

## Donate

If you enjoy using this program, please help me to continue developing it by donating some [money](http://paypal.me/drgutman/20)..
I believe in open source, but it already took me a lot of time to get it working properly and it will take a lot more to add new features.
 
<a href="http://paypal.me/drgutman/20" target="_blank">
  <img src="https://github.com/drgutman/Usei/blob/main/res/pizza.gif?raw=true" alt="Support with Pizza"/>
</a>


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=drgutman/Usei&type=Date)](https://www.star-history.com/#drgutman/Usei&Date)

