# Sistema Distribuído de Gerenciamento de Produtos

Este projeto implementa um sistema distribuído para gerenciamento de produtos com sincronização entre múltiplas filiais. O sistema é composto por uma API principal e um serviço de sincronização.

## Autor
**Moisés Silva de Azevedo**  
Universidade Federal do Mato Grosso do Sul, Câmpus de Três Lagoas (UFMS/CPTL)  
Sistemas de Informação - Computação Distribuída  
Novembro de 2025

## Arquitetura do Sistema

O projeto está dividido em dois componentes principais:

1. **API (`/api`)** - Serviço principal que gerencia produtos e pedidos (Porta 4444)
2. **Sync Service (`/sync-service`)** - Serviço de sincronização entre filiais (Porta 4000)

### Funcionalidades Implementadas

- ✅ Criação de produtos
- ✅ Replicação de dados entre filiais
- ✅ Tolerância a falhas
- ✅ Consulta de produtos
- ✅ Processamento de pedidos com controle de concorrência
- ✅ Atualização de produtos
- ✅ Sistema de autenticação JWT
- ✅ Sistema de locks para prevenção de condições de corrida
- ✅ Publicação e consumo de eventos de sincronização

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter instalado:

- **Python 3.8+**
- **pip** (gerenciador de pacotes Python)

## Configuração do Ambiente

### 1. Clone ou baixe o projeto

```bash
git clone [URL_DO_REPOSITORIO]
cd p2
```

### 2. Instale as dependências da API

```bash
cd api
pip install -r requirements.txt
```

### 3. Instale as dependências do Sync Service

```bash
cd ../sync-service
pip install fastapi uvicorn requests pydantic
```

## Executando o Sistema

O sistema deve ser executado em **duas etapas**, na seguinte ordem:

### 1. Primeiro: Execute o Sync Service

```bash
cd sync-service
python sync_service.py
```

O serviço estará disponível em: `http://localhost:4000`

### 2. Segundo: Execute a API

Em um **novo terminal**, execute:

```bash
cd api
python app.py
```

A API estará disponível em: `http://localhost:4444`

## Credenciais de Acesso

Para acessar os endpoints protegidos, use as seguintes credenciais:

- **Username**: `admin`
- **Password**: `admin123`

## Endpoints da API

### Autenticação

- `POST /login` - Realizar login e obter token JWT

### Produtos

- `POST /product` - Criar novo produto
- `GET /product/{id}` - Consultar produto por ID
- `PATCH /product/{id}` - Atualizar saldo do produto

### Pedidos

- `POST /place-order` - Realizar pedido com múltiplos itens
- `GET /order/{id}` - Consultar detalhes do pedido

### Notificações (Interno)

- `POST /notify` - Receber notificações do serviço de sincronização

## Endpoints do Sync Service

- `POST /subscribe` - Inscrever uma filial no serviço
- `POST /event/publish` - Publicar evento para sincronização
- `PATCH /event/consume/{id}` - Marcar evento como consumido
- `GET /event/non-consumed/{branch_id}` - Obter eventos não consumidos
- `POST /lock` - Criar lock para produto
- `GET /lock/{id}` - Consultar lock de produto
- `PATCH /lock/{lock_id}/release` - Liberar lock

## Exemplo de Uso

### 1. Fazer Login

```bash
curl -X POST "http://localhost:4444/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Criar Produto

```bash
curl -X POST "http://localhost:4444/product" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "initial_balance": 100}'
```

### 3. Fazer Pedido

```bash
curl -X POST "http://localhost:4444/place-order" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 5}]}'
```

## Configuração de Múltiplas Filiais

Para simular múltiplas filiais:

1. **Altere as constantes no código** de cada instância da API:
   - `BRANCH_ID`: ID único para cada filial
   - `PORT`: Porta diferente para cada filial
   - `BASE_URL`: URL base correspondente à porta

2. **Execute múltiplas instâncias** da API em portas diferentes

3. **Todas as instâncias** devem apontar para o **mesmo Sync Service** (porta 4000)

## Banco de Dados

O sistema utiliza **SQLite** com os seguintes bancos:

- `api/product_database.db` - Dados de produtos e pedidos
- `sync-service/sync_database.db` - Dados de sincronização, eventos e locks

Os bancos são criados automaticamente na primeira execução.

## Estrutura do Projeto

```
p2/
├── api/
│   ├── app.py              # Aplicação principal da API
│   ├── auth.py             # Sistema de autenticação JWT
│   ├── database.py         # Configuração do banco de dados
│   ├── event_handler.py    # Manipulação de eventos de sincronização
│   ├── models.py           # Modelos de dados Pydantic
│   ├── requirements.txt    # Dependências Python
│   └── product_database.db # Banco de dados SQLite (criado automaticamente)
├── sync-service/
│   ├── sync_service.py     # Serviço de sincronização principal
│   ├── database.py         # Configuração do banco de dados
│   ├── models.py           # Modelos de dados
│   └── sync_database.db    # Banco SQLite de sincronização (criado automaticamente)
└── README.md               # Este arquivo
```

## Troubleshooting

### Problema: Erro ao conectar com o Sync Service
**Solução**: Certifique-se de que o Sync Service está executando antes de iniciar a API.

### Problema: Produto bloqueado
**Solução**: Verifique se não há locks ativos usando o endpoint `/lock/{product_id}` do Sync Service.

### Problema: Erro de autenticação
**Solução**: Verifique se o token JWT está válido e não expirou. Faça login novamente se necessário.

### Problema: Porta já em uso
**Solução**: Verifique se não há outros serviços executando nas portas 4000 e 4444. Altere as portas se necessário.

## Desenvolvimento

Para desenvolvimento, você pode:

1. **Modificar as portas** nas constantes dos arquivos
2. **Alterar credenciais** de autenticação em `auth.py`
3. **Adicionar novos endpoints** seguindo os padrões existentes
4. **Implementar novos tipos de eventos** de sincronização

## Notas Importantes

- O sistema implementa controle de concorrência através de locks distribuídos
- Events não consumidos são recuperados automaticamente na inicialização
- Cada filial ignora eventos que ela mesma publicou
- O sistema é tolerante a falhas de rede temporárias
- Todos os endpoints (exceto login) requerem autenticação JWT