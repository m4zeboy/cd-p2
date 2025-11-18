#!/bin/bash

echo "==================================================="
echo "Sistema Distribuído de Gerenciamento de Produtos"
echo "Autor: Moisés Silva de Azevedo"
echo "UFMS/CPTL - Sistemas de Informação"
echo "Computação Distribuída - Novembro 2025"
echo "==================================================="
echo

echo "Verificando dependências..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERRO: Python não encontrado. Instale Python 3.8+ antes de continuar."
    exit 1
fi

# Detectar comando Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

echo "Python encontrado: $PYTHON_CMD"
echo

echo "Instalando dependências da API..."
cd api
$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências da API."
    exit 1
fi

echo
echo "Instalando dependências do Sync Service..."
cd ../sync-service
$PIP_CMD install fastapi uvicorn requests pydantic
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependências do Sync Service."
    exit 1
fi

cd ..
echo
echo "==================================================="
echo "Dependências instaladas com sucesso!"
echo
echo "INSTRUÇÕES PARA EXECUTAR:"
echo
echo "1. Abra um terminal e execute:"
echo "   cd sync-service"
echo "   $PYTHON_CMD sync_service.py"
echo
echo "2. Abra OUTRO terminal e execute:"
echo "   cd api"
echo "   $PYTHON_CMD app.py"
echo
echo "3. Acesse http://localhost:4444 para a API"
echo "   Acesse http://localhost:4000 para o Sync Service"
echo
echo "Credenciais: admin / admin123"
echo "==================================================="
echo
echo "Para executar automaticamente, use:"
echo "./run.sh"
