@ECHO off

SETLOCAL

SET PYTHON_EXE=TL112A_Python\tools\python.exe
SET GHS_PATH=C:\ghs\comp_201517\gbuild.exe
SET SCRIPT_FILE=TL109A_SwcSuprt\tools\swcsuprt.py

REM get parent of current component folder
FOR /D %%G in ("%CD%\..\..\..\.") DO SET PARENT_PATH=%%~fG

REM get current component folder
FOR /D %%G in ("%CD%\..\..\.") DO SET COMPONENT_PATH=%%~fG

REM get current component name
FOR %%d in ("%CD%\..\..\.") DO SET COMPONENT_NAME=%%~nxd

REM ensure we're not running from inside the template folder
FOR /D %%G in ("%CD%\..\..\.") DO IF %%~nG==ComponentTemplate GOTO template_error

REM set path to python binary
SET PYTHON_FULL_PATH=%PARENT_PATH%\%PYTHON_EXE%
IF NOT EXIST "%PYTHON_FULL_PATH%" GOTO python_error

IF NOT EXIST "%GHS_PATH%" GOTO ghs_error

REM set path to swcsuprt script
SET SCRIPT_FULL_PATH=%PARENT_PATH%\%SCRIPT_FILE%
IF NOT EXIST "%SCRIPT_FULL_PATH%" GOTO script_error

REM %PYTHON_FULL_PATH% GenFile.py

REM Get the sub level gpj
SET COMPONENT_GPJ=%COMPONENT_NAME%.gpj
IF NOT EXIST ".\..\%COMPONENT_GPJ%" GOTO gpj_error

REM Get the top level gpj
SET TOP_GPJ=%PARENT_PATH%\%COMPONENT_NAME:_Impl=_Sandbox%.gpj
IF NOT EXIST "%TOP_GPJ%" GOTO top_gpj_error

REM compile project
%GHS_PATH% -top %TOP_GPJ% %COMPONENT_GPJ% -clean -all 

%PYTHON_FULL_PATH% RunAnalysis.py ./../Polyspace/Polyspace.bf.psprj
%PYTHON_FULL_PATH% RunAnalysis.py ./../Polyspace/Polyspace.psprj

%PYTHON_FULL_PATH% check_polyspace.py

REM end script
GOTO :end


:template_error
ECHO.
ECHO This batch file isn't designed to run from the template folder.
ECHO.

GOTO :end


:python_error
ECHO.
ECHO The Python binary was not found at the expected location:
ECHO %PYTHON_FULL_PATH%
ECHO.
ECHO Download the python component, or run the SWCSupport script manually.
ECHO.
GOTO :end

:ghs_error
ECHO.
ECHO The GHS path was not found at the expected location:
ECHO %GHS_PATH%
ECHO.
ECHO install GHS in exact location.
ECHO.
GOTO :end

:gpj_error
ECHO.
ECHO The gpj project was not found at the expected location:
ECHO %COMPONENT_GPJ%
ECHO.
GOTO :end

:top_gpj_error
ECHO.
ECHO The top gpj sandbox project was not found at the expected location:
ECHO %TOP_GPJ%
ECHO.
GOTO :end


:end
ENDLOCAL

pause
