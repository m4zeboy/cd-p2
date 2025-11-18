#!/bin/bash

echo "==================================================="
echo "Sistema Distribuído de Gerenciamento de Produtos"
echo "Autor: Moisés Silva de Azevedo"
echo "UFMS/CPTL - Sistemas de Informação"
echo "Computação Distribuída - Novembro 2025"
echo "==================================================="
echo

# Detectar comando Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERRO: Python não encontrado. Instale Python 3.8+ antes de continuar."
    exit 1
fi

echo "Usando Python: $PYTHON_CMD"
echo

# Função para limpar processos ao sair
cleanup() {
    echo
    echo "Parando serviços..."
    kill $SYNC_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    echo "Serviços parados."
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

echo "Iniciando Sync Service..."
cd sync-service
$PYTHON_CMD sync_service.py &
SYNC_PID=$!
cd ..

# Aguardar um momento para o sync service inicializar
sleep 3

echo "Iniciando API..."
cd api
$PYTHON_CMD app.py &
API_PID=$!
cd ..

echo
echo "==================================================="
echo "✅ Serviços iniciados com sucesso!"
echo
echo "🔗 API: http://localhost:4444"
echo "🔗 Sync Service: http://localhost:4000"
echo
echo "👤 Credenciais: admin / admin123"
echo
echo "📖 Documentação da API: http://localhost:4444/docs"
echo "📖 Documentação do Sync: http://localhost:4000/docs"
echo
echo "💡 Pressione Ctrl+C para parar os serviços"
echo "==================================================="
echo

# Aguardar indefinidamente
wait
