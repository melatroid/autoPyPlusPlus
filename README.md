# autoPy++ Compiler Setup & Usage Guide
**autopyplusplus.wordpress.com**  
**Version 2.25**

---
## Important!

**Overwrite `myProject.apyscript` to set the opening project for AutoPy++.**
## Installation for Windows 10/11

1. **Install Git (if not already installed):**
   https://git-scm.com/download/win

2. **Install Python 3.10 or newer (if not already installed):**  
   https://www.python.org/downloads/windows/

3. **Repository clone:**  
  Open Command Prompt (cmd) or PowerShell and enter
   ```cmd/ powershell
   git clone https://github.com/melatroid/autoPyPlusPlus.git
   cd autoPyPlusPlus

4. **Install Requiremnts**
    ```cmd/ powershell
    pip install -r requirements.txt
   
6. **Start autoPy++**
   ```cmd/ powershell
   python autoPyPlusPlus.py

 
---

## More Important!

Before you use this software:

> This software is currently under development.  
> **Backup your files before you start compiling!** Errors in the software or incorrect flags could delete your files!  
> It can contain bugs that crash your whole system... use it carefully.  
> Send us error reports with detailed text and screenshots to: dseccg@gmail.com

---

## 1.) Go to IDE console and install the following packages:

```bash
pip install pyinstaller    # Python -> exe          -> direct result
pip install nuitka         # Python -> C -> exe     -> direct result
pip install cython         # Python -> C/C++        -> needs runtime DLLs and GCC compiler
pip install pyarmor        # Trial mode, buy license: https://pyarmor.readthedocs.io/en/latest/licenses.html#terms-of-use -> direct
```

Check the installed paths with:

```bash
where pyinstaller
where pyarmor
where nuitka
where cython
```

---

## 2.) Open `extensions_path.ini` with a text editor

---

## 3.) Insert correct paths to the `.exe` files, for example:

```
C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\pyinstaller.exe
C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\pyarmor.exe
C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\nuitka.cmd
C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\cython.exe
TCL:\Program Files (x86)\YOUR_IDE\tcl
```

---

## 4.) Replace the links to the `.exe` files accordingly.

---

## 5.) Put all files from AutoPy++ into a new folder.

---

# For GCC/G++ Users Only

Install full MSYS2 (includes MinGW-w64):  
https://www.msys2.org/

- GCC is for C files  
- G++ is for C++ files

### MSYS2 commands:

```bash
pacman -Syu
pacman -Su
pacman -S mingw-w64-x86_64-toolchain
pacman -S mingw-w64-x86_64-python
pacman -S python-devel
exit
```

### Check versions:

```bash
gcc --version
g++ --version
python --version
echo $MSYSTEM
```

---

# Hints and Errors

### Software Updates

- Make sure your personal file `extensions_path.ini` is backed up somewhere.
- Only backup the complete `src` folder.
- Ensure new paths for software features are inside your ini file (via Load Config in main GUI).
- Save your custom `.apyscript` file and replace it after updates.
- Every update rollout starts with tests that could fail.

---

# Practice

- For clean usage, **do not change existing names or paths of files** — create new projects instead.
- Press the "Save As" button often when making changes to settings.

---

# PyArmor Usage

To use PyArmor, include the following in your Python code:

```python
from pyarmor_runtime import __pyarmor__
__pyarmor__(__name__, __file__, b'\x28\x83\x20\x58....')
```

---

# GCC/G++ Notes

If you have problems with missing `.dll` files, set the compiler path to the global system path under Windows 10/11.

Example PowerShell commands (run as admin):

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\msys64\mingw64\bin", [EnvironmentVariableTarget]::Machine)
echo $env:Path
g++ --version
gcc --version
```

---

# Status

| Component   | Status                       |
|-------------|------------------------------|
| PyInstaller | works well (not fully tested)|
| PyArmor     | works well (not fully tested)|
| Nuitka      | works (not fully tested)     |
| Cython      | works well (not fully tested)|
| Inspector   | works well                   |
| GPP/GCC     | not working (buggy)          |
| Secure_compilers | coming soon             |

---

# Known Bugs

**Hard Bugs:**

- Permission denied when compiling spec files:  
  WARNING: Execution of '_append_data_to_exe'  
- Error with `test_01_no_gui`:  
  Command `'C:/msys64/mingw64/bin/g++.exe' ... returned non-zero exit status 1`

**Low Bugs:**

- GCC/GPP DLL files not found (see GCC/GPP section)  
- Issues with missing binary libraries (not critical)  
- Nuitka created exe files detected by antivirus (temporarily disable antivirus)

---

# Versions

### Preview Version 2.26

- Inspector reads specific logs on top  
- Switch between C or C++ compiler  
- GCC/GPP improved GUI for pipeline with Cython

### Version 2.25

- GCC/GPP editor new functions  
- Advanced build settings for GPP and Cython  
- Better pipelining with Cython (not working)

### Version 2.24

- General bug fixes  
- Bugfix for Cython C++ output  
- Choose GCC or G++ (preview)

### Version 2.23

- Direct Cython to GCC compiler pipeline  
- Compiler autodetect  
- C++ files autodetect  
- New and better GCC GUI with compiler flags

### Version 2.22

- Cython -> C -> GCC -> exe pipeline  
- All compilers updated for fallback logic via `extensions_path.ini`  
- MinGW/GCC (preview)

---

# Summary

- PyInstaller: stable and working  
- PyArmor: working but not fully tested  
- Nuitka: working (not fully tested)  
- Cython: integrated with advanced features  
- GCC/GPP: still buggy, ongoing work

---

*End of README*
