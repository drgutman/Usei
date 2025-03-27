# USEI TTS
有声 - adjective - voiced

---

![USEI TTS Logo](https://github.com/drgutman/Usei/blob/main/res/_usei.gif)

## USEI TTS is a PyQt6 interface based on the [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx).

  After much effort and bug-fixing, it's finally ready for release!<br>
  (so many bugs, soooo many. I understand now why most open source projects are CLI based)<br>
  This is my first public project (and my first commit, on my bday even 🥳).<br> 


<a href="https://github.com/drgutman/Usei/blob/main/res/Screenshot%202025-03-27%20173154.png?raw=true" target="_blank">
  <img src="https://github.com/drgutman/Usei/blob/main/res/Screenshot%202025-03-27%20173154.png?raw=true" alt="Screenshot" width="450"/>
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

  Breaks long texts into chunks and allows on the fly playback.
  
- **No-Multi Platform Support, Yet**:

  Unfortunately, it is currently available for Windows (I don't have an Apple computer to test it). 

## Installation

  The first time when you're going to run the program it will take some time to install some bigger packages that I didn't want to include in the installer and to download the model files, but after that it should load pretty quickly.

### Windows
#### WARNING - It will probably be flagged by the windows defender or any antivirus that you have. That happens because it doesn't have an official signature registered. I don't have the money to pay for it (it's like 500$, ridiculous) 

#### Installer

1. Download the latest version from [[link](https://github.com/drgutman/Usei/releases/download/v1.0.0/Usei_Setup.exe)].
2. Follow the installation prompts.
3. Ensure Python 3.12.9 is installed and added to your PATH.
4. Enjoy!



#### Portable Executable

1. Download the zip file from [[link](https://github.com/drgutman/Usei/releases/download/v1.0.0/usei_portable.7z)].
2. Ensure Python 3.12.9 is installed before running the application (it might crash your system if it is not installed).
3. Unpack it in a folder and run the executable.

#### As a Python Script

1. **Requirements**:
   - Python 3.12.9 (ensure "Add Python to PATH" is checked during installation).
   - Visual Studio Build Tools (select "Desktop development with C++" during installation).

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

## Next Steps

- [ ] Find and fix any remaining bugs.
- [ ] Implement GPU/CPU switching.
- [ ] Add streaming support.
- [ ] Integrate podcast functionality.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please open an issue or start a discussion.

## Donate

If you enjoy using this program, please help me to continue developing it by donating some money.
I believe in open source but it already took me a lot of time to get it working properly and it will take a lot more to add new features.
 
<a href="http://paypal.me/drgutman/20" target="_blank">
  <img src="https://github.com/drgutman/Usei/blob/main/res/pizza.gif?raw=true" alt="Support with Pizza"/>
</a>


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=drgutman/Usei&type=Date)](https://www.star-history.com/#drgutman/Usei&Date)

