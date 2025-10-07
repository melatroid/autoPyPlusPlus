<img src="https://nexosoft-engineering.de/autopyplusplus/git.png" alt="Alt-Text" width="250" />


# Version 2.45

# Status

| Component   | Status                        |
|-------------|-------------------------------|
| Sphinx      | works (not fully tested)      |
| Pytest      | works (not fully tested)      |
| PyInstaller | works well (not fully tested) |
| PyArmor     | works well (not fully tested) |
| Nuitka      | works      (not fully tested) |
| Cython      | works well (not fully tested) |
| MSVC        | works well (not fully tested) |
| Inspector   | works well                    |
| Secure_compilers | coming soon              |

```
📜 .py
├── 🔨 [PyInstaller] → 💾 .exe (Standalone bundled application)
├── 🔒 [PyArmor] → 🔐 .pyc (Encrypted bytecode, requires PyArmor runtime)
├── ⚙️ [Nuitka]
│   ├── 💾 .exe (Standalone or dependent executable)
│   ├── 🔌 .pyd / .so (Python extension module)
│   └── 🔗 .dll (Rare, Windows DLL)
├── 🛠️ [Cython] → 📄 .c / .cpp → [C/C++ Compiler]
│   ├── 🔌 .pyd (Windows) / .so (Linux/Mac) (Extension module)
│   ├── 💾 .exe (Native executable, rare)
│   ├── 🔗 .dll (Windows DLL, rare)
│   └── 📚 .lib (Static library for C/C++)
└── 📖 [Sphinx] → 🌐 HTML / 📄 PDF / 📚 LaTeX / 📑 man-pages
    ├── ⚡ Uses `conf.py`
    ├── 🔗 Edit your conf.py 
    ├── 📂 Output in `_build/<builder>` (e.g. `_build/html`)
    └── 🎨 Supports pip-installed and custom themes
```

# Known Bugs

**Hard Bugs:**
- Permission denied when compiling spec files:  
  WARNING: Execution of '_append_data_to_exe'  

**Low Bugs:**
- Issues with missing binary libraries (not critical)  
- Nuitka created exe files detected by antivirus (read practice lesson)

---

# Setup & Usage Guide

---
## Important!

**Overwrite `myProject.apyscript` to set the home project for AutoPy++.**


## Installation for Windows 10/11

1. **Install Git (if not already installed):**
   https://git-scm.com/download/win

2. **Install Python 3.10 or newer (if not already installed):**  
   https://www.python.org/downloads/windows/

3. **Repository clone:**  
  Open Command Prompt (cmd) or PowerShell and enter
   ```cmd/ powershell
   git clone https://github.com/melatroid/autoPyPlusPlus.git
   cd c:\pathto\autoPyPlusPlus

4. **Install Requirements**
    ```cmd/ powershell
    pip install -r requirements.txt
   
5. **Start autoPy++**
   ```cmd/ powershell
   cd c:\pathto\autoPyPlusPlus
   python autoPyPlusPlus.py

6. **Alternative Start autoPy++**
   ```cmd/ powershell
   cd c:\pathto\autoPyPlusPlus
   windows_start.bat
   (Create a shortcut from this to your desktop and change icon to src\autoPy++.ico)
   
7. **Update autoPy++ to newer version**
   ```cmd/ powershell
   cd c:\pathto\autoPyPlusPlus
   git pull origin main
   pip install -r requirements.txt --upgrade
---

## More Important!

Before you use this software:

> This software is currently under development.  
> **Backup your files before you start compiling!** Errors in the software or incorrect flags could delete your files!  
> It can contain bugs that crash your whole system... use it carefully.  
> Send us error reports with detailed text and screenshots to: info@nexosoft-engineering.de

---

## 1.) Install over Requirements.txt or go to IDE console and install the following packages:

```bash
pip install pyinstaller   
pip install nuitka        
pip install cython        
pip install pyarmor        
pip install pytest
pip install sphinx   
```

Check the installed paths with:

```bash
where pyinstaller
where pyarmor
where nuitka
where cython
where pytest
where sphinx
```

---

## 2.) Open Extensions in main gui and add your favorites

---

## 3.) Replace the links to the `.exe` files accordingly.

---

# For MSVC Pipeline Users Only

**Install full development libarys C++** 
- Needet compiler for Windows Applications is MSVC
- https://visualstudio.microsoft.com/de/visual-cpp-build-tools/
  
**How to start MSVC with autoPy++ ?** 
- edit msvc_start.bat with your paths.
- start msvc_start.exe

**Add your MSVC Compiler to Extensions** 
Open under Windows.: x64 Native Tools Command Prompt for VS 2022
```bash
where cl
```


### ONLY FOR MINGW -> MSYS2 commands:
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
- Ensure new paths for software features are inside your ini file (via Load Config in main GUI).
- Save your custom `.apyscript` file and replace it after updates.
- Every update rollout starts with tests that could fail.
---

# Practice

- For clean usage, **do not change existing names or paths of files** — create new projects instead.
- Press the "Save" button often when making changes in your project settings.

---

# Simplex-API Usage

- Set a flag to ON (or any truthy value listed below) to trigger the action.
- The watcher detects a rising edge (OFF -> ON) and runs the action once.
- If AutoReset=true, the watcher will write the flag back to OFF after firing.

Accepted truthy values: 1, true, on, yes, y, an, ein, aktiv, start
Accepted falsy values : 0, false, off, no, n, aus, stop
Optional settings:
Mode        : A | B | C       (compile mode to apply before actions)
ThreadCount : integer >=1     (clamped to [1..max threads] in GUI)
AutoReset   : true | false    (true = write flag back to OFF after trigger)

Notes:
; - Place this file in the working directory that the GUI uses.
```python
[Simplex]
Compile_all = OFF
Inspector = OFF
DeleteLogs = OFF
AutoReset = true
```
---

# Nuitka Usage

To startup nuitka compiled .exe files you need to,
set your compiled .exe file and folder in your Antivirus to secure.
Avira Antivir is usefull here.
Normaly you need a code sign certification, to start
witout changing any properties in your scanner.
```python
set the nutika path like this, direct to primary python installation
nuitka = "C:\Program Files (x86)\Thonny\python.exe"
the system found nuitka in your python version
```
---
# PyArmor Usage

To use PyArmor, include the following in your Python code:

```python
from pyarmor_runtime import __pyarmor__
__pyarmor__(__name__, __file__, b'\x28\x83\x20\x58....')
```
---
# Sphinx Usage

AutoPy++ builds documentation with [Sphinx](https://www.sphinx-doc.org/).

- **conf.py**  
  Your original Sphinx config. Never modified.

- **conf_autopy.py**  
  Created by AutoPy++ GUI. Loaded *after* `conf.py` and overrides settings.

- **Loading order**  
  1. `conf.py` (base config)  
  2. `conf_autopy.py` (GUI overrides: theme, extensions, options)

- **Themes**  
  - Install via pip (`pip install sphinx_rtd_theme`) → set in GUI.  
  - Custom themes: add path in `conf.py` → can still override in GUI.  

- **Result**  
  Base config stays intact. GUI changes are applied via `conf_autopy.py`.  
  Delete `conf_autopy.py` to revert to pure `conf.py`.


---
# MSVC Python Extension Usage
- Start msvc_start.bat
- Activate cython in script
- Target Type: Python Extension
- Activate cython C++ Pipepline
- Open C++ Pipline
- Target Type: Python Extension
- Insert python3XX.dll
- add include & libary dirs from python
- add Libaries: python3XX

If you have problems with missing python extensions, load yourextension.pyd
in with this nice tool.:
```link
https://github.com/lucasg/Dependencies
```
That will show you missing files and more.

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


















