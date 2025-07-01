
1.) go to ide console:

-pip install pyinstaller   (Python -> exe)   	    ->direct result
-pip install nuitka        (Python -> c -> exe)     ->direct result
-pip install cython        (Python -> c/c++)        ->result need runtime dlls and compilation with gcc compiler
-pip install pyarmor (Trial Modus, buy a Licence = https://pyarmor.readthedocs.io/en/latest/licenses.html#terms-of-use) ->direct

-where pyinstaller
-where pyarmor
-where nuitka
-where cython

2.) Open the extensions_path.ini with Texteditor 

3.) Insert correct path to the .exe: 

    C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\pyinstaller.exe
    C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\pyarmor.exe
    C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\nuitka.cmd
    C:\Users\[USERNAME]\AppData\Roaming\Python\Python310\Scripts\cython.exe
    TCL:\Program Files (x86)\YOUR_IDE\tcl

4.) Replace the link to the .exe

5.) Put all files from Autopy++ to a new Folder.

###################################################
For GCC/GPP Users only.:
###################################################
Install full mingw64 -> https://www.msys2.org/

GCC is for C-Files
G++ is for C++-Files

MSYS2.:
- pacman -Syu
- pacman -Su
- pacman -S mingw-w64-x86_64-toolchain
- pacman -S mingw-w64-x86_64-python 
- pacman -S python-devel
- close

MSYS2. MinGW 64-bit:
- gcc --version
- python --version
- echo $MSYSTEM

###################################################
                  HINTS AND ERRORS
###################################################
                  SoftwareUpdates
###################################################
Make shure that your pesonal file that called "extensions_path.ini" is backuped anywhere.

1.) Only Backup "src" Folder completly
2.) Be shure that new paths for software featueres are inside of your ini-file. -> load config - main gui
3.) Save your home apiscipt-file for your customizing, after update replace it.
4.) Every Update rollout starts with tests, they could be failed.

###################################################
                      Practice
###################################################
1.) For Best and Clean using, dont change already existing names or paths to diffrent files -> create new project
2.) Press "Save as" Button often, if you take changes on settings  

###################################################
                      Pyarmor
###################################################
To use Pyarmor you need this in your pycode:
------------------------------------------
from pyarmor_runtime import __pyarmor__
__pyarmor__(__name__, __file__, b'\x28\x83\x20\x58....')
------------------------------------------

###################################################
                      GCC/GPP
###################################################
If you have Problems with founding .dll files, set the Compiler to global system path under windows 11/10.
Look for the correct path to your gcc/gpp compiler

PowerShell as Admin:
- [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\msys64\mingw64\bin", [EnvironmentVariableTarget]::Machine)
- echo $env:Path
- g++ --version
- gcc --version 


###################################################
                    Important!
###################################################
Overwrite myProject.apyscript to set the Opening project for autoPy++

More Important!:
Bevor you using this Software.:
This Software is currently under development.
Backup your files before you start compiling, errors in the software or incorrectly flags could be delete your files!
It can contain Bugs that crash your hole System... use it carefully
Send us error reports with detailed text and screenshots to dseccg@gmail.com

###################################################
                      Status
###################################################
Pyinstaller:      works well (not fully tested)
PyArmor:          works well (not fully tested)
Nuitka:       	  works      (not fully tested)  
Cython:       	  works well (not fully tested) 
Inspector:    	  works well
GPP/GCC:          not works  (buggy)
Secure_compilers: coming soon

Hard Bugs:
- Permisson denied with compiling spec files -> WARNING: Execution of '_append_data_to_exe'
- Error with test_01_no_gui: Command '['C:/msys64/mingw64/bin/g++.exe', '-O2', '-o', ....returned non-zero exit status 1.

Low-Bugs:
- GCC/GPP dll files not found -> look up under GCC/CPP
- Problems with losing binäry libarys (not a critical error) 
- nuitka created exe files was detected by antivirus (close your antivirus temporary)

###################################################

                      Versions
###################################################

----Preview----------------Version 2.26 ::
- Inspector could reads specific logs on top
- switch between c oder c++ compiler
- gcc/gpp ,better gui for Pipeline with cython 

---------------------------Version 2.25 ::
- gcc/gpp editor new functions
- advancd Building Settings for gpp and cython building
- better pipelining with Cython (not works)

---------------------------Version 2.24 ::
- Bugfixes generally
- Bugfix Cython C++ Output
- Choose GCC or G++ (preview)

---------------------------Version 2.23 ::
- Direct Cython to gcc Compiler Pipeline
- Compiler Autodetect
- C++ Files Autodetect
- New and Better gcc gui, with Compiler flags 

---------------------------Version 2.22 ::
- Cython -> C -> GCC -> .Exe Pipeline
- All Compiler need update for fallback logic -> Extensions Path.ini logic
- Mingw/GCC: (Preview)

---------------------------Version 2.21 ::
- new Cython Gui =) yeahah
- Cython could pack .dll for your runtime like. python310.dll or tkinter.dll

---------------------------Version 2.20 ::
- Added a simple Windows bash starter
- nutika.exe -> nuitka.cmd
- New Extensions Path.ini logic -> Use paths before fallback, to default IDE
- Bugfix Pyinstaller path was wrong
- Better Compiler Exceptions

---------------------------Version 2.16 ::
- Cython comp. integration
- Cython advanced feautures
- Read .pyx files

---------------------------Version 2.15 ::
- Cython (preview)
- Mode C is available
- Colors Mode C
- Pyinstaller now runs directly in newest python Version

---------------------------Version 2.14 ::
- nuitka comp. new and better
- log delete __pycache__

---------------------------Version 2.13 ::
- nutika (betaversion)
- nuitka Editor new gui
- nuitka comp. integration
- Modeswitch for color Bugfix

---------------------------Version 2.12 ::
- nuitka Editor (new)
- Bug Fixes Window Managment

---------------------------Version 2.11 ::
- nuitka Editor (preview)
- Works py->pyarmor->pyinstaller->exe  (gui/console tested) =) 
- Bug fixes PyArmor /distfolder /better Parameter
- Older Bug Fixes, like inspector Jumper

---------------------------Version 2.10 ::
-Compiler update
-py -> Pyarmor -> pyinstaller -> exe  (works, not fully testet)
-Include Pyarmor Runtime in pyinstaller (only pyarmor build need this)

---------------------------Version 2.09 ::
-Bux Fixes Update
-Pyarmor Tests
-Pyarmor Dist Folder Bug fixed (Different Folders)
-Modus A/B Switch Bug fixed

---------------------------Version 2.08 ::
-Features Update
-Analyzer for Editor
-Bouncing Buttons fix (not Finally)
-Security Level Features
-New Pyarmor Featuers
-New Pyarmor Comp.
-Better Pyarmor Gui

---------------------------Version 2.07 ::
-Helper for AutoPy++
-HotKeys for faster handling
-Better Inspector Functions
-Line runner fix in Inspector

---------------------------Version 2.06 ::
-Startup with Testfiles / Add Testfolder 
-Better Exception Managing
-Helper for Editors
-fix Save as-> Spec Export 
-Big Bug Fix- Main, Editor, Inspector
-Syntax Highlight

---------------------------Version 2.05 ::
-New Gui 
-Add Symbols
---------------------------Version 2.04 ::
-CPP Save Compiler Preview
-Advanced Debug Inspector
-Set Source Directory
-Set Outputname  
-Better Design
---------------------------Version 2.03 ::
-"Load as" decleration
-"Export as" decleration
-Show log files bevor erase
-Erase build Folder Option
-Erase spec. Option
-Load/edit/save as .spec is vanilla
-Better Design
-GUI fixes
-Logfile reporter
---------------------------Version 2.02 ::
-Better Compiler Debugging
-Animations about software Status
-Direct log after export
---------------------------Version 2.01 ::
-Better Compiler debugs
-compiler to single classes
-TCL Options 	off/on	     
-Spec files parsing/Building (bumpy,not tested)
-Better GUI
-Better Design
-reengineering project files 
-import your autopy++ ini files
-new colorthemes

pyinstaller works (stable,bumpy)
pyarmor           (-not tested)

---------------------------Version 2.00 ::
-Split Modules
-Split Compilers
-Better GUI
-Import/Export Spec fix
-Switch mode A/B for more flexibility
-Free Color choice
-New Themes
-Fix a lot of Bugs
pyinstaller works stable
pyarmor works -not tested
---------------------------Version 1.5 ::
pyinstaller works stable- adds not tested
pyarmor works 
