@echo off
echo ========================================
echo   IMPORTADOR DE ESTUDIANTES
echo ========================================
echo.

REM Verificar si existe el archivo Excel
if not exist "alumnos.xlsx" (
    echo [ERROR] No se encontro el archivo alumnos.xlsx
    echo.
    echo Por favor, coloca el archivo alumnos.xlsx en esta carpeta
    echo y ejecuta este script de nuevo.
    echo.
    pause
    exit /b 1
)

echo [INFO] Archivo alumnos.xlsx encontrado
echo.

REM Instalar dependencias si es necesario
echo [INFO] Instalando dependencias necesarias...
pip install pandas openpyxl --quiet
echo.

REM Ejecutar script de importacion
echo [INFO] Iniciando importacion...
echo.
cd backend-microservices
python import_students.py
cd ..

echo.
echo ========================================
echo   IMPORTACION COMPLETADA
echo ========================================
echo.
pause
