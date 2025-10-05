@echo off
REM Batch file for Windows "Send to" menu to print with MX11
REM Supports images and text files

REM Path to your Python script (edit as needed)
set SCRIPT_PATH=%~dp0printer.py

REM Use pythonw to avoid console window, or python for debugging
set PYTHON=python

REM Detect file type and call script
if /I "%~x1"==".txt" (
    %PYTHON% "%SCRIPT_PATH%" --textfile "%~1"
) else (
    %PYTHON% "%SCRIPT_PATH%" --image "%~1"
)
