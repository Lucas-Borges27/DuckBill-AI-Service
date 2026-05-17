# DuckBill AI Service

Motor de IA do ecossistema DuckBill. Responsável por categorizar despesas automaticamente e responder perguntas financeiras com contexto do usuário.

## O que faz

| Endpoint | Função |
|---|---|
| `POST /predict` | Classifica uma descrição de despesa em categoria (TF-IDF + Logistic Regression) |
| `POST /batch-predict` | Classifica até 100 descrições em lote |
| `POST /chat` | Chat financeiro com contexto do usuário (despesas, carteira, metas). Busca web automática para perguntas sobre mercado/investimentos |
| `GET /health` | Health check do serviço e do modelo |
| `GET /model-info` | Informações técnicas do modelo |
| `GET /categories` | Lista as 12 categorias suportadas |

## Modelo de IA

- **Algoritmo:** Regressão Logística com `class_weight=balanced`
- **Vetorizador:** TF-IDF
- **Treinamento:** notebook `notebooks/CategorizacaoDuckBill.ipynb`
- **Arquivo:** `src/modelo_categorizador_bancario.pkl`
- **Acurácia:** veja `evidencias/evidenciaAcuracia.png`

## Integração com o app mobile

O app React Native (`sc-1-duckbill`) consome esta API em dois pontos:

1. **Tela de nova despesa** — ao digitar a descrição, chama `/predict` e exibe sugestão de categoria
2. **Chat DuckBill AI** — chama `/chat` com o contexto completo do usuário (despesas, carteira, metas)

## Como rodar

### Docker Hub (mais rápido)

```bash
docker run -d -p 5000:5000 borgexxx/duckbill-ai-service:latest
```

### Build local

```bash
# A partir da raiz DuckBill-AI-Service/
docker compose -f docker/docker-compose.yml up -d --build
```

### Ecossistema completo (Java + IA juntos)

```bash
# A partir da raiz Sprint4/
docker compose up -d --build
```

### Python direto (sem Docker)

```bash
cd src/
pip install -r ../docker/requirements.txt
python appClassificacao.py
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `5000` | Porta do servidor |
| `MODEL_PATH` | `modelo_categorizador_bancario.pkl` | Caminho do modelo |
| `WEB_SEARCH_ENABLED` | `true` | Habilita busca web no chat |
| `WEB_SEARCH_MAX_RESULTS` | `5` | Máximo de resultados web |
| `LLM_BASE_URL` | *(vazio)* | URL de Ollama/OpenAI para respostas via LLM |
| `LLM_MODEL` | `llama3` | Modelo LLM a usar |
| `LLM_API_KEY` | *(vazio)* | API key (se necessário) |
| `LLM_TIMEOUT_SECONDS` | `20` | Timeout da chamada LLM |

## Testes

```bash
cd DuckBill-AI-Service/
python -m pytest tests/test_api.py -v
```

## Evidências

- `evidencias/evidenciaAcuracia.png` — acurácia do modelo treinado
- `evidencias/evidenciaRequisicao.png` — teste de requisição via Postman
- `evidencias/evidenciaDisponibilidade.png` — container Docker em execução

## Documentação completa da API

Ver `docs/API_DOCUMENTATION.md`

## Autores

- Bruno Carlos Soares — RM 559250
- Lucas Borges de Souza — RM 560027
- Pedro Henrique da Silva — RM 560393
