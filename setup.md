# Setup do Terabyte Challenge

## Configuração com Docker

### 1. Configurar variáveis de ambiente

**Arquivo: `.env` (na raiz do projeto)**

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:6000/postgres

# Chat Settings
MAX_HISTORY_MESSAGES=10
MAX_SIMILAR_MESSAGES=3
SIMILARITY_THRESHOLD=0.3

# API Settings
API_TITLE=Terabyte Challenge Chat API
API_DESCRIPTION=API de chat with LLM, vector search e function calling
API_VERSION=1.0.0

# Models
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

**⚠️ IMPORTANTE:** Substitua `your_openai_api_key_here` pela sua chave real da OpenAI!

### 2. Estrutura de arquivos necessária

```
projeto/
├── .env                    # Arquivo de configuração (raiz)
├── docker/
│   ├── docker-compose.yaml # Configuração do Docker
│   ├── Dockerfile          # Imagem da FastAPI
│   └── init.sql           # Script de inicialização do BD
├── api/                   # Código da aplicação
├── requirements.txt       # Dependências Python
└── ...
```

### 3. Executar com Docker

```bash
# Na pasta docker/
cd docker

# Subir os serviços (PostgreSQL + FastAPI)
docker-compose up -d

# Ver logs da aplicação
docker-compose logs -f fastapi

# Ver logs do banco
docker-compose logs -f postgresql

# Parar os serviços
docker-compose down

# Parar e remover volumes (limpa o banco)
docker-compose down -v
```

### 4. Verificar se está funcionando

- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/
- **PostgreSQL**: localhost:6000

### 5. Executar sem Docker (desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt

# Subir apenas o PostgreSQL
cd docker
docker-compose up postgresql -d

# Executar a API localmente (na raiz do projeto)
cd ..
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Funcionalidades Disponíveis

### Endpoints da API

- `GET /` - Health check e status
- `POST /chat` - Enviar mensagem para o chat
- `GET /conversations` - Listar conversas
- `GET /conversations/{id}` - Detalhes da conversa
- `POST /search` - Busca semântica
- `DELETE /conversations/{id}` - Deletar conversa

### Tools Disponíveis

1. **Calculator** - Cálculos matemáticos
2. **Get Current DateTime** - Data/hora atual
3. **Text Analyzer** - Análise de texto
4. **Search Knowledge Base** - Base de conhecimento

### Exemplo de uso

```bash
# Testar o chat
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Quanto é 15 * 23?"
  }'
```

## Troubleshooting

### Problema: API não consegue conectar no banco
- Verifique se o PostgreSQL está rodando: `docker-compose ps`
- Verifique os logs: `docker-compose logs postgresql`

### Problema: Erro de API Key
- Confirme se a `OPENAI_API_KEY` está configurada no `.env`
- Verifique se a chave é válida

### Problema: Dependências não encontradas
- Rebuild da imagem: `docker-compose build --no-cache fastapi`

### Problema: Porta em uso
- Mude as portas no `docker-compose.yaml` se necessário