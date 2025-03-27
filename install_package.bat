@echo on
REM This BAT file installs missing packages using the system Python,
REM installing them into an "external_packages" folder next to the executable.

echo Current directory: %CD%
echo Batch file location: %~dp0
echo Installing packages: %*

set target_dir=%~dp0..\external_packages
echo Target directory: %target_dir%

if not exist "%target_dir%" (
    echo Creating directory: %target_dir%
    mkdir "%target_dir%"
)

REM Check if directory was created
if not exist "%target_dir%" (
    echo ERROR: Failed to create directory %target_dir%
    exit /b 1
)

echo Running pip installation...
python -m pip install --no-cache-dir --upgrade --target "%target_dir%" %*
set RESULT=%ERRORLEVEL%

echo Pip returned: %RESULT%
echo Installation completed with status %RESULT%

dir "%target_dir%"

exit /b %RESULT%