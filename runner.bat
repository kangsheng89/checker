@ECHO off

SETLOCAL

SET PYTHON_EXE=TL112A_Python\tools\python.exe

REM get parent of current component folder
FOR /D %%G in ("%CD%\..\..\..\.") DO SET PARENT_PATH=%%~fG

REM set path to python binary
SET PYTHON_FULL_PATH=%PARENT_PATH%\%PYTHON_EXE%
IF NOT EXIST "%PYTHON_FULL_PATH%" GOTO python_error

%PYTHON_FULL_PATH% RunAnalysis.py ./../Polyspace/Polyspace.bf.psprj
IF %ERRORLEVEL% NEQ 0 (EXIT /B 1)

%PYTHON_FULL_PATH% RunAnalysis.py ./../Polyspace/Polyspace.psprj
IF %ERRORLEVEL% NEQ 0 (EXIT /B 1)

%PYTHON_FULL_PATH% check_polyspace.py
IF %ERRORLEVEL% NEQ 0 (EXIT /B 1)

REM end script
GOTO :end


:python_error
ECHO.
ECHO The Python binary was not found at the expected location:
ECHO %PYTHON_FULL_PATH%
ECHO.
ECHO Download the python component, or run the SWCSupport script manually.
ECHO.
EXIT /B 3

:end
ENDLOCAL