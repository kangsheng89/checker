@ECHO off

SETLOCAL

SET GHS_PATH=C:\ghs\comp_201517\gbuild.exe

REM get parent of current component folder
FOR /D %%G in ("%CD%\..\..\..\.") DO SET PARENT_PATH=%%~fG

REM get current component folder
FOR /D %%G in ("%CD%\..\..\.") DO SET COMPONENT_PATH=%%~fG

REM get current component name
FOR %%d in ("%CD%\..\..\.") DO SET COMPONENT_NAME=%%~nxd

IF NOT EXIST "%GHS_PATH%" GOTO ghs_error

REM Get the sub level gpj
SET COMPONENT_GPJ=%COMPONENT_NAME%.gpj
IF NOT EXIST ".\..\%COMPONENT_GPJ%" GOTO gpj_error

REM Get the top level gpj
SET TOP_GPJ=%PARENT_PATH%\%COMPONENT_NAME:_Impl=_Sandbox%.gpj
IF NOT EXIST "%TOP_GPJ%" GOTO top_gpj_error

REM compile project
%GHS_PATH% -top %TOP_GPJ% %COMPONENT_GPJ% -clean -all 

IF %ERRORLEVEL% NEQ 0 (EXIT /B 1)
REM end script
GOTO :end

:ghs_error
ECHO.
ECHO The GHS path was not found at the expected location:
ECHO %GHS_PATH%
ECHO.
ECHO install GHS in exact location.
ECHO.
EXIT /B 3

:gpj_error
ECHO.
ECHO The gpj project was not found at the expected location:
ECHO %COMPONENT_GPJ%
ECHO.
EXIT /B 3

:top_gpj_error
ECHO.
ECHO The top gpj sandbox project was not found at the expected location:
ECHO %TOP_GPJ%
ECHO.
EXIT /B 3

:end
ENDLOCAL

