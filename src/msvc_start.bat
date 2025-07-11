@echo off
REM Start MSVC-Environment 
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
REM Start autoPy++
SET PYTHON_PATH="C:\Program Files (x86)\Thonny\python.exe"
cd /d C:\Users\melatroid\Desktop\autoPy++\AutoPyPlusPlus\src
%PYTHON_PATH% -m AutoPyPlusPlus
pause
