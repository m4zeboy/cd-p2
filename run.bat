@echo off
setlocal

echo ===================================================
echo Sistema Distribuido de Gerenciamento de Produtos
echo Autor: Moises Silva de Azevedo
echo UFMS/CPTL - Sistemas de Informacao
echo Computacao Distribuida - Novembro 2025
echo ===================================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Instale Python 3.8+ antes de continuar.
    pause
    exit /b 1
)

echo Usando Python:
python --version
echo.

echo Iniciando Sync Service...
cd sync-service
start "Sync Service" cmd /k "python sync_service.py"

REM Aguardar um momento para o sync service inicializar
timeout /t 3 /nobreak >nul

cd ..\api
echo Iniciando API...
start "API Service" cmd /k "python app.py"

cd ..
echo.
echo ===================================================
echo ✅ Servicos iniciados com sucesso!
echo.
echo 🔗 API: http://localhost:4444
echo 🔗 Sync Service: http://localhost:4000
echo.
echo 👤 Credenciais: admin / admin123
echo.
echo 📖 Documentacao da API: http://localhost:4444/docs
echo 📖 Documentacao do Sync: http://localhost:4000/docs
echo.
echo 💡 Feche as janelas de comando para parar os servicos
echo ===================================================
echo.
pause
