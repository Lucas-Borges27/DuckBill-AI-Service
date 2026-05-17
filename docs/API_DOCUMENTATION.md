# 📚 DuckBill AI - Documentação da API

## Visão Geral

A API DuckBill AI fornece endpoints REST para classificação automática de despesas usando Machine Learning. O serviço utiliza um modelo de Regressão Logística com vetorização TF-IDF para categorizar descrições de transações bancárias.

**Base URL:** `http://localhost:5000`

**Versão:** 2.0.0

---

## 🔐 Autenticação

Atualmente, a API não requer autenticação. Em produção, recomenda-se implementar autenticação via API Key ou OAuth2.

---

## 📋 Endpoints

### 1. Home / Informações da API

**Endpoint:** `GET /`

**Descrição:** Retorna informações gerais sobre a API e seus endpoints disponíveis.

**Resposta de Sucesso (200):**
```json
{
  "service": "DuckBill AI - Classificação Inteligente de Despesas",
  "version": "2.0.0",
  "status": "online",
  "model_loaded": true,
  "endpoints": {
    "health": "/health",
    "predict": "/predict (POST)",
    "batch_predict": "/batch-predict (POST)",
    "model_info": "/model-info",
    "categories": "/categories"
  },
  "documentation": "https://github.com/seu-usuario/DuckBill-AI-Service"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/
```

---

### 2. Health Check

**Endpoint:** `GET /health`

**Descrição:** Verifica o status de saúde da API e se o modelo está carregado.

**Resposta de Sucesso (200):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-05-14T22:30:00.000Z",
  "service": "DuckBill AI Service"
}
```

**Resposta de Erro (503):**
```json
{
  "status": "unhealthy",
  "model_loaded": false,
  "timestamp": "2024-05-14T22:30:00.000Z",
  "service": "DuckBill AI Service"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/health
```

**Uso:** Ideal para monitoramento e health checks em sistemas de orquestração (Kubernetes, Docker Swarm).

---

### 3. Listar Categorias

**Endpoint:** `GET /categories`

**Descrição:** Retorna todas as categorias de despesas disponíveis no modelo.

**Resposta de Sucesso (200):**
```json
{
  "categories": [
    "Food & Dining",
    "Shopping",
    "Entertainment",
    "Transportation",
    "Bills & Utilities",
    "Health & Fitness",
    "Travel",
    "Education",
    "Personal Care",
    "Gifts & Donations",
    "Business Services",
    "Other"
  ],
  "total": 12
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/categories
```

---

### 4. Informações do Modelo

**Endpoint:** `GET /model-info`

**Descrição:** Retorna informações técnicas sobre o modelo de IA.

**Resposta de Sucesso (200):**
```json
{
  "model_type": "Pipeline (TF-IDF + Logistic Regression)",
  "pipeline_steps": ["tfidf", "logreg"],
  "categories_count": 12,
  "input_format": "text/string",
  "output_format": "category + confidence",
  "training_info": {
    "algorithm": "Logistic Regression",
    "vectorizer": "TF-IDF",
    "class_weight": "balanced",
    "max_iterations": 1000
  }
}
```

**Resposta de Erro (503):**
```json
{
  "error": "Modelo não carregado"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/model-info
```

---

### 5. Predição Individual

**Endpoint:** `POST /predict`

**Descrição:** Classifica uma única descrição de despesa.

**Corpo da Requisição:**
```json
{
  "description": "McDonalds Big Mac"
}
```

**Parâmetros:**
- `description` (string, obrigatório): Descrição da despesa (2-500 caracteres)

**Resposta de Sucesso (200):**
```json
{
  "description": "McDonalds Big Mac",
  "category": "Food & Dining",
  "confidence": 0.9234,
  "top_predictions": [
    {
      "category": "Food & Dining",
      "confidence": 0.9234
    },
    {
      "category": "Shopping",
      "confidence": 0.0456
    },
    {
      "category": "Other",
      "confidence": 0.0310
    }
  ],
  "timestamp": "2024-05-14T22:30:00.000Z",
  "status": "success"
}
```

**Respostas de Erro:**

**400 - Descrição ausente:**
```json
{
  "error": "Por favor, envie 'description' no JSON",
  "example": {"description": "McDonalds Big Mac"},
  "status": "error"
}
```

**400 - Descrição inválida:**
```json
{
  "error": "Descrição muito curta (mínimo 2 caracteres)",
  "status": "error"
}
```

**503 - Modelo não disponível:**
```json
{
  "error": "Modelo não disponível",
  "status": "error"
}
```

**Exemplos:**

**cURL:**
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"description": "Starbucks Coffee"}'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:5000/predict",
    json={"description": "Netflix Monthly Subscription"}
)
print(response.json())
```

**JavaScript:**
```javascript
fetch('http://localhost:5000/predict', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({description: 'Uber ride to office'})
})
.then(response => response.json())
.then(data => console.log(data));
```

---

### 6. Predição em Lote

**Endpoint:** `POST /batch-predict`

**Descrição:** Classifica múltiplas descrições de despesas em uma única requisição (máximo 100).

**Corpo da Requisição:**
```json
{
  "descriptions": [
    "McDonalds",
    "Netflix",
    "Uber",
    "Shell Gas"
  ]
}
```

**Parâmetros:**
- `descriptions` (array de strings, obrigatório): Lista de descrições (1-100 itens)

**Resposta de Sucesso (200):**
```json
{
  "total_processed": 4,
  "successful": 4,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "description": "McDonalds",
      "category": "Food & Dining",
      "confidence": 0.9123
    },
    {
      "index": 1,
      "description": "Netflix",
      "category": "Entertainment",
      "confidence": 0.8956
    },
    {
      "index": 2,
      "description": "Uber",
      "category": "Transportation",
      "confidence": 0.9345
    },
    {
      "index": 3,
      "description": "Shell Gas",
      "category": "Transportation",
      "confidence": 0.8734
    }
  ],
  "errors": null,
  "timestamp": "2024-05-14T22:30:00.000Z",
  "status": "success"
}
```

**Resposta com Erros Parciais (200):**
```json
{
  "total_processed": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "index": 0,
      "description": "Valid description",
      "category": "Shopping",
      "confidence": 0.8234
    },
    {
      "index": 2,
      "description": "Another valid",
      "category": "Food & Dining",
      "confidence": 0.9012
    }
  ],
  "errors": [
    {
      "index": 1,
      "description": "a",
      "error": "Descrição muito curta (mínimo 2 caracteres)"
    }
  ],
  "timestamp": "2024-05-14T22:30:00.000Z",
  "status": "success"
}
```

**Respostas de Erro:**

**400 - Array ausente:**
```json
{
  "error": "Por favor, envie 'descriptions' (array) no JSON",
  "example": {"descriptions": ["McDonalds", "Netflix", "Uber"]},
  "status": "error"
}
```

**400 - Muitos itens:**
```json
{
  "error": "Máximo de 100 descrições por requisição",
  "status": "error"
}
```

**Exemplos:**

**cURL:**
```bash
curl -X POST http://localhost:5000/batch-predict \
  -H "Content-Type: application/json" \
  -d '{
    "descriptions": [
      "Starbucks Coffee",
      "Netflix Subscription",
      "Uber Trip"
    ]
  }'
```

**Python:**
```python
import requests

descriptions = [
    "McDonalds Big Mac",
    "Netflix Monthly",
    "Uber to Airport",
    "Shell Gas Station"
]

response = requests.post(
    "http://localhost:5000/batch-predict",
    json={"descriptions": descriptions}
)
print(response.json())
```

---

### 7. Chat Financeiro

**Endpoint:** `POST /chat`

**Descrição:** Responde perguntas financeiras com base no contexto real do usuário. Para perguntas sobre mercado, Selic, investimentos e tendências, realiza busca na web automaticamente para enriquecer a resposta. Se uma URL de LLM estiver configurada (`LLM_BASE_URL`), usa o modelo de linguagem; caso contrário, responde com lógica baseada em regras.

**Corpo da Requisição:**
```json
{
  "message": "Quais são meus maiores gastos?",
  "context": {
    "usuario": { "nome": "Lucas", "id": 1 },
    "despesas": [
      { "categoriaId": 2, "valor": 350.00, "descricao": "Supermercado" }
    ],
    "carteira": [
      { "ticker": "PETR4", "financeiroLiquido": 1200.00 }
    ],
    "metas": [
      { "titulo": "Viagem", "valorObjetivo": 5000, "valorGuardado": 1200 }
    ],
    "categorias": [
      { "id": 2, "nome": "Alimentacao" }
    ]
  }
}
```

**Parâmetros:**
- `message` (string, obrigatório): Pergunta do usuário (2–500 caracteres)
- `context` (objeto, opcional): Dados do usuário para personalizar a resposta

**Resposta de Sucesso (200):**
```json
{
  "answer": "Lucas, analisei suas despesas e a categoria com maior peso é Alimentacao, somando R$ 350,00...",
  "intent": "despesas",
  "status": "success",
  "message": "Quais são meus maiores gastos?",
  "timestamp": "2024-05-17T10:00:00.000Z"
}
```

**Valores possíveis de `intent`:** `despesas`, `investimentos`, `metas`, `educacao`, `geral`, `llm`

**Exemplo cURL:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Me dê dicas de investimento",
    "context": { "usuario": { "nome": "Lucas" }, "despesas": [], "carteira": [], "metas": [] }
  }'
```

---

## 🔍 Validações de Entrada

### Descrição de Despesa

- **Tipo:** String
- **Tamanho mínimo:** 2 caracteres
- **Tamanho máximo:** 500 caracteres
- **Obrigatório:** Sim
- **Processamento:** Convertido para minúsculas antes da predição

### Batch Predict

- **Tipo:** Array de strings
- **Tamanho mínimo:** 1 item
- **Tamanho máximo:** 100 itens
- **Obrigatório:** Sim

---

## 📊 Códigos de Status HTTP

| Código | Significado | Descrição |
|--------|-------------|-----------|
| 200 | OK | Requisição bem-sucedida |
| 400 | Bad Request | Dados de entrada inválidos |
| 404 | Not Found | Endpoint não encontrado |
| 500 | Internal Server Error | Erro interno do servidor |
| 503 | Service Unavailable | Modelo não carregado ou serviço indisponível |

---

## 🎯 Categorias de Despesas

O modelo classifica despesas nas seguintes categorias:

1. **Food & Dining** - Restaurantes, fast food, cafés, delivery
2. **Shopping** - Compras em lojas, e-commerce, varejo
3. **Entertainment** - Streaming, cinema, jogos, eventos
4. **Transportation** - Uber, táxi, combustível, transporte público
5. **Bills & Utilities** - Contas de luz, água, internet, telefone
6. **Health & Fitness** - Farmácia, academia, consultas médicas
7. **Travel** - Hotéis, passagens, turismo
8. **Education** - Cursos, livros, material escolar
9. **Personal Care** - Salão, spa, produtos de beleza
10. **Gifts & Donations** - Presentes, doações, caridade
11. **Business Services** - Serviços profissionais, consultoria
12. **Other** - Outras despesas não categorizadas

---

## 💡 Boas Práticas

### 1. Tratamento de Erros
Sempre verifique o código de status HTTP e o campo `status` na resposta:

```python
response = requests.post(url, json=data)
if response.status_code == 200:
    result = response.json()
    if result.get('status') == 'success':
        # Processar resultado
        pass
else:
    # Tratar erro
    error = response.json().get('error')
```

### 2. Uso de Batch Predict
Para múltiplas predições, use `/batch-predict` em vez de múltiplas chamadas a `/predict`:

```python
# ❌ Evite
for desc in descriptions:
    predict(desc)

# ✅ Prefira
batch_predict(descriptions)
```

### 3. Validação de Confiança
Considere a confiança da predição ao tomar decisões:

```python
result = predict("ambiguous description")
if result['confidence'] < 0.7:
    # Solicitar confirmação manual
    pass
```

### 4. Health Check
Implemente health checks periódicos em produção:

```python
import time

def wait_for_service():
    while True:
        try:
            health = requests.get("http://api/health")
            if health.json().get('model_loaded'):
                break
        except:
            pass
        time.sleep(5)
```

---

## 🔧 Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `PORT` | Porta do servidor | 5000 |
| `FLASK_ENV` | Ambiente (production/development) | production |
| `MODEL_PATH` | Caminho do arquivo .pkl do modelo | modelo_categorizador_bancario.pkl |

---

## 📈 Limites e Performance

- **Timeout:** 30 segundos por requisição
- **Batch máximo:** 100 descrições por requisição
- **Taxa de requisições:** Sem limite (recomenda-se rate limiting em produção)
- **Tempo médio de resposta:** 
  - Predição individual: ~50ms
  - Batch (100 itens): ~500ms

---

## 🐛 Troubleshooting

### Erro: "Modelo não carregado"
**Causa:** O arquivo .pkl não foi encontrado ou está corrompido.
**Solução:** Verifique se o arquivo `modelo_categorizador_bancario.pkl` está no diretório correto.

### Erro: "Descrição muito curta"
**Causa:** A descrição tem menos de 2 caracteres.
**Solução:** Envie uma descrição mais detalhada.

### Erro: Connection refused
**Causa:** O servidor não está rodando.
**Solução:** Inicie o servidor com `python src/appClassificacao.py` ou `docker-compose up`.

---

## 📞 Suporte

Para dúvidas ou problemas:
- **GitHub Issues:** [Link do repositório]
- **Email:** seu-email@exemplo.com
- **Documentação:** Este arquivo

---

## 📝 Changelog

### v2.0.0 (Sprint 4)
- ✨ Adicionado endpoint `/batch-predict`
- ✨ Adicionado endpoint `/model-info`
- ✨ Adicionado endpoint `/categories`
- ✨ Top 3 predições no endpoint `/predict`
- 🔒 Validação robusta de entrada
- 📝 Logging estruturado
- 🐛 Melhor tratamento de erros

### v1.0.0 (Sprint 3)
- 🎉 Lançamento inicial
- ✨ Endpoint `/predict`
- ✨ Endpoint `/health`
- 🐳 Containerização Docker

---

**Última atualização:** Maio 2024  
**Versão da API:** 2.0.0  
**Sprint:** 4 - FIAP Challenge