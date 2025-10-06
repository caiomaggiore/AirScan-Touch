@echo off
echo ========================================
echo AirScan Control v1.1 - Instalacao
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
echo   python AirScan_Control_v1.1.py
echo.
echo Para calibracao v1.1 (multi-nivel):
echo   python airscan_calibration_v1.1.py
echo.
echo Niveis disponiveis:
echo   - BASICO (5 pontos, ~25s)
echo   - AVANCADO (9 pontos, ~45s)
echo   - PROFISSIONAL (13 pontos, ~65s)
echo.
pause
