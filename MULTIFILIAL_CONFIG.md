# Configuração de Múltiplas Filiais

Este documento explica como configurar e executar múltiplas filiais do sistema distribuído simultaneamente.

## Visão Geral

Para simular um ambiente com múltiplas filiais, você precisará:

1. **Um único Sync Service** (porta 4000)
2. **Múltiplas instâncias da API**, cada uma representando uma filial diferente

## Configuração Passo a Passo

### 1. Preparar os Arquivos para Cada Filial

Para cada filial adicional, você deve criar uma cópia da pasta `api` com configurações específicas:

```bash
# Criar filiais
cp -r api filial-centro
cp -r api filial-norte  
cp -r api filial-sul
```

### 2. Configurar Cada Filial

Em cada pasta de filial, edite o arquivo `app.py` e modifique as seguintes constantes:

#### Filial Centro (Porta 4444)
```python
BRANCH_ID = "bb5942cb28ff48f3420f0c13e9187746"  # Original
PORT = 4444
BASE_URL = f"http://localhost:{PORT}"
```

#### Filial Norte (Porta 4445)
```python
BRANCH_ID = "aa1234cb28ff48f3420f0c13e9187746"  # Novo ID único
PORT = 4445
BASE_URL = f"http://localhost:{PORT}"
```

#### Filial Sul (Porta 4446)
```python
BRANCH_ID = "cc5678cb28ff48f3420f0c13e9187746"  # Novo ID único  
PORT = 4446
BASE_URL = f"http://localhost:{PORT}"
```

### 3. Gerar IDs Únicos para Filiais

Para gerar novos BRANCH_IDs únicos, use Python:

```python
import uuid
print(uuid.uuid4().hex)
```

### 4. Executar o Sistema Completo

#### Passo 1: Iniciar o Sync Service
```bash
cd sync-service
python sync_service.py
```

#### Passo 2: Iniciar Cada Filial (em terminais separados)

**Terminal 2 - Filial Centro:**
```bash
cd filial-centro
python app.py
```

**Terminal 3 - Filial Norte:**
```bash
cd filial-norte
python app.py
```

**Terminal 4 - Filial Sul:**
```bash
cd filial-sul
python app.py
```

## Testando a Sincronização

### 1. Fazer Login em Cada Filial

**Filial Centro (4444):**
```bash
curl -X POST "http://localhost:4444/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Filial Norte (4445):**
```bash
curl -X POST "http://localhost:4445/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Criar Produto na Filial Centro

```bash
curl -X POST "http://localhost:4444/product" \
  -H "Authorization: Bearer SEU_TOKEN_CENTRO" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "initial_balance": 100}'
```

### 3. Verificar Sincronização na Filial Norte

```bash
curl -X GET "http://localhost:4445/product/1" \
  -H "Authorization: Bearer SEU_TOKEN_NORTE"
```

### 4. Fazer Pedido na Filial Sul

```bash
curl -X POST "http://localhost:4446/place-order" \
  -H "Authorization: Bearer SEU_TOKEN_SUL" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 5}]}'
```

### 5. Verificar Atualização em Todas as Filiais

O saldo do produto deve estar atualizado em todas as filiais.

## Scripts de Automação para Múltiplas Filiais

### Script Linux/Mac (multifilial.sh)

```bash
#!/bin/bash

# Configurar filiais
setup_filiais() {
    echo "Configurando filiais..."
    
    # Filial Norte
    mkdir -p filial-norte
    cp -r api/* filial-norte/
    sed -i 's/BRANCH_ID = "bb5942cb28ff48f3420f0c13e9187746"/BRANCH_ID = "aa1234cb28ff48f3420f0c13e9187746"/' filial-norte/app.py
    sed -i 's/PORT = 4444/PORT = 4445/' filial-norte/app.py
    
    # Filial Sul
    mkdir -p filial-sul
    cp -r api/* filial-sul/
    sed -i 's/BRANCH_ID = "bb5942cb28ff48f3420f0c13e9187746"/BRANCH_ID = "cc5678cb28ff48f3420f0c13e9187746"/' filial-sul/app.py
    sed -i 's/PORT = 4444/PORT = 4446/' filial-sul/app.py
}

# Executar serviços
run_services() {
    echo "Iniciando Sync Service..."
    cd sync-service && python3 sync_service.py &
    sleep 3
    
    echo "Iniciando Filial Centro (4444)..."
    cd ../api && python3 app.py &
    sleep 2
    
    echo "Iniciando Filial Norte (4445)..."
    cd ../filial-norte && python3 app.py &
    sleep 2
    
    echo "Iniciando Filial Sul (4446)..."
    cd ../filial-sul && python3 app.py &
    
    echo "Todos os serviços iniciados!"
    echo "Centro: http://localhost:4444"
    echo "Norte: http://localhost:4445"  
    echo "Sul: http://localhost:4446"
    echo "Sync: http://localhost:4000"
    
    wait
}

# Executar
setup_filiais
run_services
```

## Monitoramento das Filiais

### Verificar Status de Todas as Filiais

```bash
# Script para verificar se todas as filiais estão ativas
check_filiais() {
    echo "Verificando status das filiais..."
    
    echo -n "Sync Service (4000): "
    curl -s http://localhost:4000/docs >/dev/null && echo "✅ Online" || echo "❌ Offline"
    
    echo -n "Filial Centro (4444): "
    curl -s http://localhost:4444/docs >/dev/null && echo "✅ Online" || echo "❌ Offline"
    
    echo -n "Filial Norte (4445): "
    curl -s http://localhost:4445/docs >/dev/null && echo "✅ Online" || echo "❌ Offline"
    
    echo -n "Filial Sul (4446): "
    curl -s http://localhost:4446/docs >/dev/null && echo "✅ Online" || echo "❌ Offline"
}
```

## Cenários de Teste

### 1. Teste de Concorrência
- Fazer pedidos simultâneos do mesmo produto em filiais diferentes
- Verificar que apenas uma operação por vez é processada (sistema de locks)

### 2. Teste de Sincronização
- Criar produtos em diferentes filiais
- Verificar que todos aparecem em todas as filiais

### 3. Teste de Tolerância a Falhas
- Parar uma filial temporariamente
- Fazer alterações em outras filiais
- Reiniciar a filial e verificar sincronização automática

## Troubleshooting

### Problema: Filiais não sincronizam
**Solução**: Verificar se todas as filiais têm BRANCH_IDs únicos e se o Sync Service está executando.

### Problema: Erro de porta em uso
**Solução**: Verificar se as portas estão livres antes de iniciar as filiais:
```bash
netstat -tulpn | grep :4444
netstat -tulpn | grep :4445
netstat -tulpn | grep :4446
```

### Problema: Locks não liberados
**Solução**: Verificar locks ativos no Sync Service e liberar manualmente se necessário.

## Considerações de Produção

1. **Banco de Dados**: Em produção, use PostgreSQL ou MySQL ao invés de SQLite
2. **Configuração**: Use variáveis de ambiente para configurações
3. **Logs**: Implementar logging centralizado
4. **Monitoramento**: Adicionar health checks e métricas
5. **Segurança**: Configurar HTTPS e autenticação mais robusta