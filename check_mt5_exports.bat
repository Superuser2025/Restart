@echo off
REM Quick Check - Find EA Export Files
echo ================================================
echo Checking MT5 Files Directory for EA Exports
echo ================================================
echo.

set MT5_PATH=C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Files

if not exist "%MT5_PATH%" (
    echo ERROR: MT5 Files directory not found!
    echo Expected: %MT5_PATH%
    echo.
    pause
    exit /b 1
)

echo Found MT5 Files directory: %MT5_PATH%
echo.
echo Searching for JSON files...
echo.

dir /s /b "%MT5_PATH%\*.json" 2>nul

if errorlevel 1 (
    echo.
    echo WARNING: No JSON files found!
    echo EA may not be exporting data.
    echo.
) else (
    echo.
    echo ================================================
    echo Found JSON files above ^
    echo Showing recent modifications...
    echo ================================================
    echo.
    dir /o-d /s "%MT5_PATH%\*.json"
)

echo.
echo ================================================
pause
