@echo off
REM Find Active EA Location
echo ============================================================
echo Finding Your Active EA
echo ============================================================
echo.

set MT5_EXPERTS=C:\Users\Shukra\AppData\Roaming\MetaQuotes\Terminal\D80F6A7780D6E8F57AE2A0827BF4AF18\MQL5\Experts

if not exist "%MT5_EXPERTS%" (
    echo ERROR: MT5 Experts directory not found!
    echo Expected: %MT5_EXPERTS%
    pause
    exit /b 1
)

echo Checking compiled EA files (.ex5)...
echo.

cd /d "%MT5_EXPERTS%"

echo Looking for InstitutionalTradingRobot_v3.ex5...
echo.

if exist "InstitutionalTradingRobot_v3.ex5" (
    echo FOUND: InstitutionalTradingRobot_v3.ex5
    echo Location: %MT5_EXPERTS%\InstitutionalTradingRobot_v3.ex5
    echo.
    echo File details:
    dir "InstitutionalTradingRobot_v3.ex5" | find "InstitutionalTradingRobot"
    echo.

    echo This is your COMPILED EA - currently running.
    echo.
    echo To find the SOURCE file (.mq5):
    echo 1. Open MT5
    echo 2. Press F4 (MetaEditor)
    echo 3. Right-click InstitutionalTradingRobot_v3 in Navigator
    echo 4. Click "Open Containing Folder"
    echo.
) else (
    echo WARNING: InstitutionalTradingRobot_v3.ex5 not found!
    echo.
    echo Searching for ANY .ex5 files...
    dir /b *.ex5
    echo.
)

echo ============================================================
echo.
echo All Expert files in this directory:
echo.
dir /b *.ex5 2>nul
echo.

echo ============================================================
echo.
echo To modify your EA:
echo 1. Find the source file using Method 1 above
echo 2. Copy JSONExporter.mqh to the same directory
echo 3. Make changes following ML_INTEGRATION_GUIDE.md
echo 4. Press F7 to recompile
echo.
echo ============================================================

pause
