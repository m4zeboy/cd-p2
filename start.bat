@echo off
echo ===================================================
echo Sistema Distribuido de Gerenciamento de Produtos
echo Autor: Moises Silva de Azevedo
echo UFMS/CPTL - Sistemas de Informacao
echo Computacao Distribuida - Novembro 2025
echo ===================================================
echo.

echo Verificando dependencias...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Instale Python 3.8+ antes de continuar.
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Instalando dependencias da API...
cd api
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias da API.
    pause
    exit /b 1
)

echo.
echo Instalando dependencias do Sync Service...
cd ..\sync-service
pip install fastapi uvicorn requests pydantic
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias do Sync Service.
    pause
    exit /b 1
)

cd ..
echo.
echo ===================================================
echo Dependencias instaladas com sucesso!
echo.
echo INSTRUCOES PARA EXECUTAR:
echo.
echo 1. Abra um terminal e execute:
echo    cd sync-service
echo    python sync_service.py
echo.
echo 2. Abra OUTRO terminal e execute:
echo    cd api
echo    python app.py
echo.
echo 3. Acesse http://localhost:4444 para a API
echo    Acesse http://localhost:4000 para o Sync Service
echo.
echo Credenciais: admin / admin123
echo ===================================================
pause
