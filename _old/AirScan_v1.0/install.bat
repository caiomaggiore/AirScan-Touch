@echo off
echo ========================================
echo AirScan Control v1.0 - Instalacao
echo ========================================
echo.

echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo Para iniciar o sistema:
echo   python airscan_control.py
echo.
echo Para calibracao:
echo   python airscan_calibration.py
echo   ou pressione Shift+C no sistema principal
echo.
pause
