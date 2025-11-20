@echo off
echo ========================================
echo Sistema de Asistencias - Inicio Rapido
echo ========================================
echo.
echo IMPORTANTE: Asegurese de haber ejecutado install-dependencies.bat primero
echo.
echo Iniciando servicios...
echo.

echo [1/5] Iniciando Users Service (Puerto 8101)...
start "Users Service" cmd /k "cd backend-microservices\users-service && python app.py"
timeout /t 3 /nobreak >nul

echo [2/5] Iniciando Events Service (Puerto 8102)...
start "Events Service" cmd /k "cd backend-microservices\events-service && python app.py"
timeout /t 3 /nobreak >nul

echo [3/5] Iniciando Reports Service (Puerto 8103)...
start "Reports Service" cmd /k "cd backend-microservices\reports-service && python app.py"
timeout /t 3 /nobreak >nul

echo [4/5] Iniciando API Gateway (Puerto 8100)...
start "API Gateway" cmd /k "cd backend-microservices\api-gateway && python app.py"
timeout /t 5 /nobreak >nul

echo [5/5] Iniciando Frontend (Puerto 5173)...
start "Frontend React" cmd /k "cd frontend-final && npm run dev"

echo.
echo ========================================
echo SISTEMA INICIADO CORRECTAMENTE
echo ========================================
echo.
echo Acceda al sistema en: http://localhost:5173
echo.
echo CREDENCIALES:
echo - Admin: admin / admin123
echo - Encargado: encargado / encargado123
echo - Estudiante: estudiante / estudiante123
echo.
echo Presione cualquier tecla para cerrar...
pause >nul
