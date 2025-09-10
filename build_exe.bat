@echo off
echo Building OmniLauncher Executable...
echo.

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable
pyinstaller --clean OmniLauncher.spec

echo.
echo Build completed!
echo.

REM Check if exe was created
if exist "dist\OmniLauncher\OmniLauncher.exe" (
    echo Executable created successfully: dist\OmniLauncher\OmniLauncher.exe
    echo.
    echo To run the application, use: dist\OmniLauncher\OmniLauncher.exe
) else (
    echo Error: Executable was not created.
)

pause
