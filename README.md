<img src="https://autopyplusplus.wordpress.com/wp-content/uploads/2025/05/autopy-2.png" alt="Alt-Text" width="100" />

# Version 2.30
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
> Send us error reports with detailed text and screenshots to: dseccg@gmail.com

---

## 1.) Install over Requirements.txt or go to IDE console and install the following packages:

```bash
pip install pyinstaller   
pip install nuitka        
pip install cython        
pip install pyarmor        

```

Check the installed paths with:

```bash
where pyinstaller
where pyarmor
where nuitka
where cython
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

| Component   | Status                        |
|-------------|-------------------------------|
| PyInstaller | works well (not fully tested) |
| PyArmor     | works well (not fully tested) |
| Nuitka      | works      (not fully tested) |
| Cython      | works well (not fully tested) |
| MSVC        | works      (not fully tested) |
| Inspector   | works well                    |
| Secure_compilers | coming soon              |
|
```
📜 .py
├── 🔨 [PyInstaller] → 💾 .exe (Standalone bundled application)
├── 🔒 [PyArmor] → 🔐 .pyc (Encrypted bytecode, requires PyArmor runtime)
├── ⚙️ [Nuitka]
│   ├── 💾 .exe (Standalone or dependent executable)
│   ├── 🔌 .pyd / .so (Python extension module)
│   └── 🔗 .dll (Rare, Windows DLL)
└── 🛠️ [Cython] → 📄 .c / .cpp → [C/C++ Compiler]
    ├── 🔌 .pyd (Windows) / .so (Linux/Mac) (Extension module)
    ├── 💾 .exe (Native executable, rare)
    ├── 🔗 .dll (Windows DLL, rare)
    └── 📚 .lib (Static library for C/C++)
```

# Known Bugs

**Hard Bugs:**
- Permission denied when compiling spec files:  
  WARNING: Execution of '_append_data_to_exe'  

**Low Bugs:**
- Issues with missing binary libraries (not critical)  
- Nuitka created exe files detected by antivirus (temporarily disable antivirus)

---
# Versions
### (Preview) Version 2.31
- Inspector reads specific logs on top

### (latest) Version 2.30
- cython ready for building standalone executables
- msvc ready for building standalone executables
  
### Version 2.29
- MSVC pipeline with Cython for pyd builds 
- Big Bugfixes in msvc editor
- better pipeline with msvc
- add testfiles in cpp and pyd

### Version 2.28
- Gui Update for Cython and Pipeline
- Autocollect attributs in older Apyscript Projects

### Version 2.27
- add msvc as new primary c++ compiler
- New Extensions Editor
- Big Bug fix Update for Gui

### Version 2.26
- better windows_start.bat
- add core functions
- Save current Project Button
- Load/Store for extensions_path.ini
- Project name is output name ...

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

### Version 2.21
- Neue Cython GUI  
- Cython kann Runtime-DLLs (z.B. python310.dll, tkinter.dll) packen  

### Version 2.20
- Einfacher Windows Bash Starter hinzugefügt  
- `nutika.exe` wird zu `nuitka.cmd`  
- Neue Extensions Path.ini Logik (Priorität vor Fallback auf IDE)  
- Bugfix: Falscher PyInstaller-Pfad behoben  
- Verbesserte Compiler-Ausnahmen  

### Version 2.16
- Integration des Cython Compilers  
- Erweiterte Features für Cython  
- Unterstützung für `.pyx` Dateien  

### Version 2.15
- Cython (Preview)  
- Modus C verfügbar  
- Farbmodi für Modus C  
- PyInstaller läuft nun direkt in neuester Python-Version  

### Version 2.14
- Neue und verbesserte Nuitka Compilerintegration  
- Log-Löschung für `__pycache__`  


### Version 2.13
- Beta-Version von Nuitka („nutika“)  
- Neue GUI für Nuitka Editor  
- Integration des Nuitka Compilers  
- Bugfix für Farbmodus  


### Version 2.12
- Neue GUI für Nuitka Editor  
- Bugfixes im Window Management  


### Version 2.11
- Nuitka Editor Preview  
- Funktioniert: py -> pyarmor -> pyinstaller -> exe (GUI/Console getestet)  
- Bugfixes: PyArmor / Dist-Folder / Parameter  
- Diverse ältere Bugfixes, z.B. Inspector Jumper  

### Version 2.10
- Compiler Update  
- py -> PyArmor -> PyInstaller -> exe Workflow funktioniert (nicht vollständig getestet)  
- PyArmor Runtime in PyInstaller eingebunden (nur PyArmor-Builds benötigen das)  

### Version 2.09
- Bugfixes und Updates  
- PyArmor Tests  
- Bugfix Dist-Folder bei PyArmor (verschiedene Ordner)  
- Bugfix für Modus A/B Switch  

### Version 2.08
- Feature Updates  
- Analyzer für Editor  
- Button Bounce Fix (nicht final)  
- Sicherheitslevel Features  
- Neue PyArmor Features & Compiler  
- Verbesserte PyArmor GUI  

### Version 2.07
- Helfer für AutoPy++  
- Hotkeys für schnellere Bedienung  
- Verbesserte Inspector-Funktionen  
- Fix Line Runner im Inspector  


### Version 2.06
- Start mit Testdateien / Testordner hinzugefügt  
- Verbesserte Ausnahmebehandlung  
- Helfer für Editoren  
- Fix Save As -> Spec Export  
- Große Bugfixes (Main, Editor, Inspector)  
- Syntax Highlighting  

### Version 2.05
- Neue GUI  
- Symbole hinzugefügt  

### Version 2.04
- CPP Save Compiler Preview  
- Erweiterter Debug Inspector  
- Set Source Directory  
- Set Output Name  
- Besseres Design  


### Version 2.03
- „Load as“ Deklaration  
- „Export as“ Deklaration  
- Log-Dateien vor Löschen anzeigen  
- Optionen zum Löschen von Build- und Spec-Ordnern  
- Lade/Edite/Speichere .spec vanilla  
- Verbesserungen im Design und GUI  
- Logfile Reporter  

### Version 2.02
- Verbesserte Compiler-Debugging  
- Animationen über Softwarestatus  
- Direkter Log nach Export  


### Version 2.01
- Verbesserte Compiler-Debugs  
- Compiler in einzelne Klassen aufgeteilt  
- TCL Optionen (on/off)  
- Spez-Dateien Parsing und Building (bumpy, ungetestet)  
- Verbesserte GUI und Design  
- Reengineering der Projektdateien  
- Import von AutoPy++ ini Dateien  
- Neue Farbthemen  

### Version 2.00
- Module aufgeteilt  
- Compiler aufgeteilt  
- Bessere GUI  
- Import/Export Spec Fix  
- Modus A/B für mehr Flexibilität  
- Freie Farbauswahl  
- Neue Themes  
- Viele Bugfixes  
- PyInstaller stabil  
- PyArmor (nicht getestet)  

### Version 1.5
- PyInstaller stabil (nicht getestet)  
- PyArmor funktioniert  


---

*End of README*
