@echo off
echo ========================================
echo INSTALANDO DEPENDENCIAS NUEVAS
echo ========================================
echo.

echo [1/3] Instalando pandas y openpyxl en Events Service...
cd backend-microservices\events-service
python -m pip install pandas openpyxl
echo.

echo [2/3] Instalando reportlab en Reports Service...
cd ..\reports-service
python -m pip install reportlab
echo.

echo [3/3] Verificando instalacion...
cd ..\..
echo.

echo ========================================
echo DEPENDENCIAS INSTALADAS
echo ========================================
echo.
echo Ahora puedes ejecutar: INICIO_RAPIDO.bat
echo.
pause
