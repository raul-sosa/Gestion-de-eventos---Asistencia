Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalando Dependencias del Sistema" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Instalando dependencias del Users Service..." -ForegroundColor Yellow
Set-Location backend-microservices\users-service
python -m pip install -r requirements.txt
Set-Location ..\..

Write-Host ""
Write-Host "Instalando dependencias del Events Service..." -ForegroundColor Yellow
Set-Location backend-microservices\events-service
python -m pip install -r requirements.txt
Set-Location ..\..

Write-Host ""
Write-Host "Instalando dependencias del Reports Service..." -ForegroundColor Yellow
Set-Location backend-microservices\reports-service
python -m pip install -r requirements.txt
Set-Location ..\..

Write-Host ""
Write-Host "Instalando dependencias del API Gateway..." -ForegroundColor Yellow
Set-Location backend-microservices\api-gateway
python -m pip install -r requirements.txt
Set-Location ..

Write-Host ""
Write-Host "Instalando dependencias del Frontend..." -ForegroundColor Yellow
Set-Location frontend-final
npm install
Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instalacion completada exitosamente" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar el sistema, ejecute: .\INICIO_RAPIDO.bat" -ForegroundColor White
Write-Host ""
Read-Host "Presione Enter para continuar"
