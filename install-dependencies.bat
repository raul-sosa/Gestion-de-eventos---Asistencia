@echo off
echo ========================================
echo Instalando Dependencias del Sistema
echo ========================================
echo.

echo Instalando dependencias del Users Service...
cd backend-microservices\users-service
pip install -r requirements.txt
cd ..\..

echo.
echo Instalando dependencias del Events Service...
cd backend-microservices\events-service
pip install -r requirements.txt
cd ..\..

echo.
echo Instalando dependencias del Reports Service...
cd backend-microservices\reports-service
pip install -r requirements.txt
cd ..\..

echo.
echo Instalando dependencias del API Gateway...
cd backend-microservices\api-gateway
pip install -r requirements.txt
cd ..

echo.
echo Instalando dependencias del Frontend...
cd frontend-final
call npm install
cd ..

echo.
echo ========================================
echo Instalacion completada exitosamente
echo ========================================
echo.
echo Para iniciar el sistema, ejecute: start-all-services.bat
echo.
pause
