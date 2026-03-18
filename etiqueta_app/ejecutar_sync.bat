@echo off
set PYTHON="C:\Users\SELSO\AppData\Local\Programs\Python\Python314\python.exe"
set SCRIPT="C:\Users\SELSO\PythonPrgrams\ProgramsPython\etiqueta_app\sync_automatico.py"

:: La carpeta donde está el script (para que encuentre el .json y cree la carpeta logs/)
cd /d "C:\Users\SELSO\PythonPrgrams\ProgramsPython\etiqueta_app"

%PYTHON% %SCRIPT%

:: Pausa solo si se ejecuta manualmente (doble clic), no desde el Programador de Tareas
if "%1"=="manual" pause