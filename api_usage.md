# API de Chat - Documentação de Uso

## Visão Geral

Esta API implementa um sistema de chat inteligente com as seguintes funcionalidades:
- **Memória conversacional** usando embeddings e busca por similaridade
- **Function calling** com ferramentas úteis
- **Histórico de conversas** com busca semântica
- **Vector database** para recuperação de contexto relevante

## Endpoints Principais

### 1. Health Check
```bash
GET /
```
Verifica o status da API e banco de dados.

### 2. Chat
```bash
POST /chat
```
Endpoint principal para interagir com o chatbot.

**Payload:**
```json
{
  "message": "Sua mensagem aqui",
  "conversation_id": "opcional-id-da-conversa",
  "use_history": true,
  "max_history_messages": 10
}
```

**Resposta:**
```json
{
  "response": "Resposta do assistente",
  "conversation_id": "id-da-conversa",
  "message_id": "id-da-mensagem",
  "tools_used": ["calculator", "get_current_datetime"],
  "sources_used": ["Mensagem abc123 (85.2%)"],
  "total_tokens": 150
}
```

### 3. Listar Conversas
```bash
GET /conversations?limit=20
```
Lista as conversas mais recentes.

### 4. Detalhes da Conversa
```bash
GET /conversations/{conversation_id}
```
Obtém o histórico completo de uma conversa.

### 5. Busca Semântica
```bash
POST /search
```
Busca mensagens similares usando embeddings.

**Payload:**
```json
{
  "query": "termo de busca",
  "limit": 5,
  "similarity_threshold": 0.7
}
```

## Ferramentas Disponíveis

O assistente tem acesso às seguintes ferramentas:

### 1. Calculator
Realiza cálculos matemáticos.
```
Exemplo: "Quanto é 15 * 23 + 10?"
```

### 2. Get Current DateTime
Obtém data e hora atuais.
```
Exemplo: "Que horas são?"
```

### 3. Text Analyzer
Analisa textos fornecendo estatísticas.
```
Exemplo: "Analise este texto: 'Olá mundo! Como você está?'"
```

### 4. Search Knowledge Base
Busca informações sobre tecnologia.
```
Exemplo: "Me fale sobre Python"
```

## Configuração

### 1. Variáveis de Ambiente
Crie um arquivo `.env` baseado no `.env.example`:

```bash
OPENAI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:6000/postgres
```

### 2. Banco de Dados
Execute o Docker Compose para iniciar o PostgreSQL:

```bash
cd docker
docker-compose up -d
```

### 3. Instalação
```bash
pip install -r requirements.txt
```

### 4. Execução
```bash
python -m api.main
# ou
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Exemplos de Uso

### Conversa Simples
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Como você pode me ajudar?"
  }'
```

### Usando Calculator
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quanto é 25 * 8 + 100?",
    "conversation_id": "math_session"
  }'
```

### Busca no Histórico
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python programming",
    "limit": 3,
    "similarity_threshold": 0.8
  }'
```

## Funcionalidades Avançadas

### Memória Conversacional
- Cada conversa mantém contexto histórico
- Busca automática por mensagens similares de outras conversas
- Citação de fontes quando informações do histórico são utilizadas

### Embeddings e Busca Semântica
- Todas as mensagens são convertidas em embeddings (OpenAI text-embedding-3-large)
- Busca por similaridade usando distância coseno no PostgreSQL com pgvector
- Recuperação automática de contexto relevante

### Function Calling
- Integração nativa com OpenAI function calling
- Execução automática de ferramentas quando necessário
- Suporte para múltiplas chamadas de função em uma única resposta

## Interface Web

A API também pode ser testada através da interface automática do FastAPI:
```
http://localhost:8000/docs
```

## Logs e Monitoramento

A aplicação gera logs detalhados sobre:
- Requisições recebidas
- Execução de ferramentas
- Operações no banco de dados
- Erros e exceções

## Limitações e Considerações

1. **Rate Limits**: Respeite os rate limits da OpenAI API
2. **Custos**: Monitore o uso de tokens para controlar custos
3. **Segurança**: Em produção, configure adequadamente CORS e autenticação
4. **Performance**: Para alto volume, considere cache e pooling de conexões

## Troubleshooting

### Erro de Conexão com Banco
- Verifique se o PostgreSQL está rodando
- Confirme as configurações de conexão no `.env`

### Erro de API Key
- Verifique se `OPENAI_API_KEY` está configurada corretamente
- Confirme se a chave tem permissões adequadas

### Erro de Embeddings
- Verifique se a extensão pgvector está instalada no PostgreSQL
- Confirme se as tabelas foram criadas corretamente