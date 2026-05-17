import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
import logging
from datetime import datetime
import os
import re
import json
import urllib.request
import urllib.error
import importlib

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silenciar os avisos de versão para o terminal ficar limpo
warnings.filterwarnings("ignore", category=UserWarning)

# 1. Inicializar o app Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para integração com frontends

# 2. Carregamento do Pipeline
MODEL_PATH = os.getenv('MODEL_PATH', 'modelo_categorizador_bancario.pkl')
modelo_final = None
model_loaded = False

try:
    modelo_final = joblib.load(MODEL_PATH)
    model_loaded = True
    logger.info("🦆 DuckBill Engine: Modelo carregado com sucesso!")
except Exception as e:
    logger.error(f"❌ Erro ao carregar o modelo: {e}")

LLM_BASE_URL = os.getenv('LLM_BASE_URL', '').strip()
LLM_API_KEY = os.getenv('LLM_API_KEY', '').strip()
LLM_MODEL = os.getenv('LLM_MODEL', 'llama3').strip()
LLM_TIMEOUT_SECONDS = float(os.getenv('LLM_TIMEOUT_SECONDS', '20'))
WEB_SEARCH_ENABLED = os.getenv('WEB_SEARCH_ENABLED', 'true').strip().lower() == 'true'
WEB_SEARCH_MAX_RESULTS = int(os.getenv('WEB_SEARCH_MAX_RESULTS', '5'))

# Categorias conhecidas (para validação)
CATEGORIAS_CONHECIDAS = [
    'Food & Dining', 'Shopping', 'Entertainment', 'Transportation',
    'Bills & Utilities', 'Health & Fitness', 'Travel', 'Education',
    'Personal Care', 'Gifts & Donations', 'Business Services', 'Other'
]

def validar_descricao(descricao):
    """Valida e sanitiza a descrição de entrada"""
    if not descricao or not isinstance(descricao, str):
        return None, "Descrição inválida ou vazia"
    
    descricao = descricao.strip()
    
    if len(descricao) < 2:
        return None, "Descrição muito curta (mínimo 2 caracteres)"
    
    if len(descricao) > 500:
        return None, "Descrição muito longa (máximo 500 caracteres)"
    
    return descricao, None

def normalizar_texto(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip().lower())

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def pesquisar_web(pergunta):
    if not WEB_SEARCH_ENABLED:
        return []

    try:
        modulo = importlib.import_module("duckduckgo_search")
        ddgs_class = getattr(modulo, "DDGS", None)
        if ddgs_class is None:
            return []

        with ddgs_class() as ddgs:
            resultados = list(ddgs.text(pergunta, max_results=WEB_SEARCH_MAX_RESULTS))
            web_context = []
            for item in resultados[:WEB_SEARCH_MAX_RESULTS]:
                titulo = str(item.get("title", "")).strip()
                corpo = str(item.get("body", "")).strip()
                href = str(item.get("href", "")).strip()
                if titulo or corpo:
                    web_context.append({
                        "title": titulo,
                        "snippet": corpo,
                        "url": href
                    })
            return web_context
    except Exception as error:
        logger.warning(f"Falha na busca web: {error}")
        return []

def formatar_contexto_web(resultados_web):
    if not resultados_web:
        return "Sem resultados web adicionais."

    linhas = []
    for indice, item in enumerate(resultados_web, start=1):
        titulo = item.get("title", "Sem título")
        snippet = item.get("snippet", "")
        url = item.get("url", "")
        linhas.append(f"{indice}. {titulo} | {snippet} | Fonte: {url}")
    return "\n".join(linhas)

def montar_contexto_resumido(contexto):
    despesas = contexto.get('despesas', []) if isinstance(contexto, dict) else []
    carteira = contexto.get('carteira', []) if isinstance(contexto, dict) else []
    metas = contexto.get('metas', []) if isinstance(contexto, dict) else []
    usuario = contexto.get('usuario', {}) if isinstance(contexto, dict) else {}

    nome_usuario = usuario.get('nome', 'investidor')
    total_despesas = sum(float(item.get('valor', 0) or 0) for item in despesas)
    total_carteira = sum(float(item.get('financeiroLiquido', 0) or 0) for item in carteira)

    return (
        f"Usuário: {nome_usuario}. "
        f"Total de despesas cadastradas: {len(despesas)} com soma de {formatar_moeda(total_despesas)}. "
        f"Total de ativos na carteira: {len(carteira)} com patrimônio monitorado de {formatar_moeda(total_carteira)}. "
        f"Total de metas: {len(metas)}."
    )

def gerar_prompt_llm(pergunta, contexto, resultados_web):
    contexto_resumido = montar_contexto_resumido(contexto)
    contexto_web = formatar_contexto_web(resultados_web)
    return (
        "Você é a DuckBill AI, uma assistente financeira em português do Brasil. "
        "Responda de forma clara, útil e objetiva. "
        "Use o contexto do usuário quando existir, mas também forneça dicas gerais de educação financeira e investimentos quando os dados estiverem vazios. "
        "Quando houver resultados de busca web, use essas fontes para enriquecer a resposta e cite que se baseou em fontes encontradas. "
        "Não invente rentabilidades atuais nem recomende ativos específicos como se fosse consultoria personalizada. "
        "Se faltar dado do usuário, deixe isso claro e complemente com orientação geral prática.\n\n"
        f"Contexto do usuário: {contexto_resumido}\n\n"
        f"Resultados de busca web:\n{contexto_web}\n\n"
        f"Pergunta do usuário: {pergunta}"
    )

def chamar_llm(pergunta, contexto, resultados_web):
    if not LLM_BASE_URL:
        return None

    openai_payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Você é a DuckBill AI, assistente financeira focada em educação financeira, investimentos e análise do contexto do usuário."
            },
            {
                "role": "user",
                "content": gerar_prompt_llm(pergunta, contexto, resultados_web)
            }
        ],
        "temperature": 0.4
    }

    ollama_payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Você é a DuckBill AI, assistente financeira focada em educação financeira, investimentos e análise do contexto do usuário."
            },
            {
                "role": "user",
                "content": gerar_prompt_llm(pergunta, contexto, resultados_web)
            }
        ],
        "stream": False
    }

    headers = {
        "Content-Type": "application/json"
    }

    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    candidate_requests = [
        (
            f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
            json.dumps(openai_payload).encode("utf-8")
        ),
        (
            f"{LLM_BASE_URL.rstrip('/')}/api/chat",
            json.dumps(ollama_payload).encode("utf-8")
        )
    ]

    for endpoint, request_data in candidate_requests:
        req = urllib.request.Request(endpoint, data=request_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SECONDS) as response:
                raw_body = response.read().decode("utf-8")
                body = json.loads(raw_body)

                choices = body.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return {
                            "answer": content.strip(),
                            "intent": "llm",
                            "status": "success",
                            "source": "llm"
                        }

                if isinstance(body.get("message"), dict):
                    content = body.get("message", {}).get("content")
                    if isinstance(content, str) and content.strip():
                        return {
                            "answer": content.strip(),
                            "intent": "llm",
                            "status": "success",
                            "source": "llm"
                        }
        except urllib.error.HTTPError as error:
            try:
                error_body = error.read().decode("utf-8")
            except Exception:
                error_body = str(error)
            logger.warning(f"LLM HTTP error at {endpoint}: {error.code} - {error_body}")
        except Exception as error:
            logger.warning(f"LLM unavailable at {endpoint}, using fallback: {error}")

    return None

def responder_chat(pergunta, contexto):
    pergunta_normalizada = normalizar_texto(pergunta)
    usar_web = any(token in pergunta_normalizada for token in [
        'noticia', 'notícias', 'mercado', 'hoje', 'atual', 'atualmente',
        'cenario', 'cenário', 'pesquisa', 'internet', 'web', 'tendencia', 'tendência'
    ]) or any(token in pergunta_normalizada for token in ['investimento', 'investimentos', 'selic', 'tesouro', 'cdb', 'acao', 'ações', 'fii'])

    resultados_web = pesquisar_web(pergunta) if usar_web else []
    resposta_llm = chamar_llm(pergunta, contexto, resultados_web)
    if resposta_llm:
        if resultados_web:
            fontes = [str(item.get('url')) for item in resultados_web if item.get('url')]
            if fontes:
                resposta_llm['answer'] = (
                    f"{resposta_llm['answer']}\n\n"
                    f"Fontes web consultadas:\n- " + "\n- ".join(fontes[:3])
                )
        return resposta_llm

    despesas = contexto.get('despesas', []) if isinstance(contexto, dict) else []
    carteira = contexto.get('carteira', []) if isinstance(contexto, dict) else []
    metas = contexto.get('metas', []) if isinstance(contexto, dict) else []
    usuario = contexto.get('usuario', {}) if isinstance(contexto, dict) else {}
    categorias = contexto.get('categorias', []) if isinstance(contexto, dict) else []

    nome_usuario = usuario.get('nome', 'investidor')
    total_despesas = sum(float(item.get('valor', 0) or 0) for item in despesas)
    total_carteira = sum(float(item.get('financeiroLiquido', 0) or 0) for item in carteira)

    categoria_por_id = {}
    for categoria in categorias:
        categoria_id = categoria.get('id')
        categoria_nome = categoria.get('nome')
        if categoria_id is not None and categoria_nome:
            categoria_por_id[categoria_id] = categoria_nome

    totais_categoria = {}
    for despesa in despesas:
        categoria_nome = categoria_por_id.get(despesa.get('categoriaId'), f"Categoria {despesa.get('categoriaId')}")
        totais_categoria[categoria_nome] = totais_categoria.get(categoria_nome, 0) + float(despesa.get('valor', 0) or 0)

    categorias_ordenadas = sorted(totais_categoria.items(), key=lambda item: item[1], reverse=True)
    metas_ordenadas = sorted(
        metas,
        key=lambda item: float(item.get('valorObjetivo', 0) or 0) - float(item.get('valorGuardado', 0) or 0),
        reverse=True
    )

    if any(token in pergunta_normalizada for token in ['maior gasto', 'maiores gastos', 'gasto', 'despesa', 'despesas']):
        if not despesas:
            return {
                "answer": "Ainda não encontrei despesas cadastradas para analisar. Cadastre seus gastos no Cofre para eu te mostrar padrões e categorias dominantes.",
                "intent": "despesas",
                "status": "success"
            }

        if categorias_ordenadas:
            categoria_top, valor_top = categorias_ordenadas[0]
            participacao = round((valor_top / total_despesas) * 100) if total_despesas > 0 else 0
            return {
                "answer": f"{nome_usuario}, analisei suas despesas e a categoria com maior peso é {categoria_top}, somando {formatar_moeda(valor_top)}, cerca de {participacao}% do total monitorado. Seu gasto total atual está em {formatar_moeda(total_despesas)}.",
                "intent": "despesas",
                "status": "success"
            }

    if any(token in pergunta_normalizada for token in ['investimento', 'investimentos', 'carteira', 'ativo', 'ativos']):
        pediu_dicas = any(token in pergunta_normalizada for token in ['dica', 'dicas', 'como investir', 'por onde começar', 'comecar', 'iniciar'])

        if not carteira:
            if pediu_dicas:
                return {
                    "answer": "Mesmo sem ativos cadastrados, aqui vão dicas práticas para começar a investir melhor: 1) monte uma reserva de emergência em produto de alta liquidez, como Tesouro Selic ou CDB com liquidez diária; 2) defina seu objetivo e prazo antes de escolher o investimento; 3) comece com renda fixa para ganhar segurança; 4) faça aportes mensais pequenos, mas consistentes; 5) diversifique aos poucos em vez de colocar tudo em um único ativo.",
                    "intent": "investimentos",
                    "status": "success"
                }

            return {
                "answer": "Sua carteira ainda está vazia no app. Assim que você registrar ativos no Mapa da Riqueza, eu consigo resumir concentração, patrimônio investido e sugestões. Mesmo assim, se quiser, posso te dar dicas gerais de investimento para iniciantes.",
                "intent": "investimentos",
                "status": "success"
            }

        principal_ativo = max(carteira, key=lambda item: float(item.get('financeiroLiquido', 0) or 0))
        ticker = principal_ativo.get('ticker', 'ativo principal')
        valor_principal = float(principal_ativo.get('financeiroLiquido', 0) or 0)

        if pediu_dicas:
            return {
                "answer": f"Hoje seu patrimônio investido monitorado está em {formatar_moeda(total_carteira)}. O maior peso da carteira está em {ticker}, com aproximadamente {formatar_moeda(valor_principal)}. Além do diagnóstico, minhas dicas são: revisar concentração para não depender demais de um único ativo, manter aportes recorrentes, alinhar os investimentos ao prazo dos seus objetivos e rebalancear a carteira periodicamente.",
                "intent": "investimentos",
                "status": "success"
            }

        return {
            "answer": f"Hoje seu patrimônio investido monitorado está em {formatar_moeda(total_carteira)}. O maior peso da carteira está em {ticker}, com aproximadamente {formatar_moeda(valor_principal)}. Minha dica é revisar concentração e manter aportes consistentes de acordo com seu objetivo.",
            "intent": "investimentos",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['meta', 'metas', 'objetivo', 'objetivos']):
        if not metas:
            return {
                "answer": "Você ainda não possui metas cadastradas. Se criar metas no app, eu consigo te dizer qual está mais próxima, qual precisa de mais aporte e como priorizar.",
                "intent": "metas",
                "status": "success"
            }

        meta_mais_desafiadora = metas_ordenadas[0]
        titulo = meta_mais_desafiadora.get('titulo', 'Meta principal')
        guardado = float(meta_mais_desafiadora.get('valorGuardado', 0) or 0)
        objetivo = float(meta_mais_desafiadora.get('valorObjetivo', 0) or 0)
        falta = max(objetivo - guardado, 0)

        return {
            "answer": f"Sua meta que mais exige atenção agora é '{titulo}'. Você já acumulou {formatar_moeda(guardado)} de um objetivo de {formatar_moeda(objetivo)}, faltando {formatar_moeda(falta)} para concluir.",
            "intent": "metas",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['reserva de emergencia', 'reserva', 'emergencia']):
        return {
            "answer": "Reserva de emergência é o valor separado para imprevistos, normalmente investido em produtos de alta liquidez e baixo risco. Em geral, ela deve cobrir entre 3 e 12 meses do seu custo de vida, dependendo da sua estabilidade de renda.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['renda fixa', 'cdb', 'tesouro', 'selic']):
        return {
            "answer": "Renda fixa é uma classe de investimentos mais previsível, muito usada para reserva e objetivos de curto e médio prazo. Exemplos comuns são Tesouro Selic, CDBs e LCIs/LCAs. Ela tende a oferecer menos volatilidade do que ações, embora o retorno também possa ser mais limitado.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['diversificacao', 'diversificar', 'diversificada', 'concentracao', 'concentrado']):
        return {
            "answer": "Diversificação significa distribuir seu dinheiro entre diferentes ativos, classes e riscos. Isso ajuda a reduzir o impacto de uma perda isolada. Em vez de concentrar tudo em um único ativo, o ideal é equilibrar a carteira conforme prazo, perfil e objetivo.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['juros compostos', 'juros', 'compostos']):
        return {
            "answer": "Juros compostos são os rendimentos calculados sobre o valor inicial e também sobre os rendimentos acumulados. Por isso o tempo é tão poderoso nos investimentos: quanto antes você começa e mais regular é o aporte, maior tende a ser o efeito acumulado.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['perfil', 'conservador', 'moderado', 'arrojado']):
        return {
            "answer": "Perfil de investidor indica o quanto você tolera risco e volatilidade. Conservador prioriza segurança e liquidez, moderado aceita algum risco em busca de retorno maior, e arrojado suporta oscilações mais intensas visando crescimento no longo prazo.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['rebalanceamento', 'rebalancear']):
        return {
            "answer": "Rebalancear a carteira é ajustar os percentuais dos ativos para voltar à estratégia planejada. Isso costuma ser feito quando um ativo cresce ou cai muito e altera o equilíbrio desejado entre risco, liquidez e horizonte de investimento.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['aporte', 'aportes', 'aporte mensal']):
        return {
            "answer": "Aportes recorrentes ajudam a criar disciplina e aproveitar o tempo a favor do patrimônio. Em vez de depender de grandes quantias esporádicas, investir um valor frequente e sustentável costuma ser mais eficiente para construir resultados consistentes.",
            "intent": "educacao",
            "status": "success"
        }

    if any(token in pergunta_normalizada for token in ['dica', 'dicas', 'aprender', 'investir melhor', 'conselho', 'educacao financeira']):
        return {
            "answer": "Algumas boas práticas para investir melhor: monte primeiro uma reserva de emergência, diversifique sua carteira, evite concentrar tudo em um único ativo, entenda seu perfil de risco, mantenha aportes recorrentes e pense sempre no prazo do objetivo antes de investir.",
            "intent": "educacao",
            "status": "success"
        }

    return {
        "answer": f"Olá, {nome_usuario}. Posso te ajudar com análise de despesas, carteira de investimentos, metas financeiras e educação sobre investimentos. Você pode perguntar sobre reserva de emergência, renda fixa, diversificação, juros compostos, perfil de investidor, aportes e rebalanceamento.",
        "intent": "geral",
        "status": "success"
    }

@app.route('/', methods=['GET'])
def home():
    """Endpoint raiz com informações da API"""
    return jsonify({
        "service": "DuckBill AI - Classificação Inteligente de Despesas",
        "version": "2.1.0",
        "status": "online",
        "model_loaded": model_loaded,
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "batch_predict": "/batch-predict (POST)",
            "model_info": "/model-info",
            "categories": "/categories",
            "chat": "/chat (POST)"
        },
        "documentation": "https://github.com/seu-usuario/DuckBill-AI-Service"
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check para monitoramento"""
    return jsonify({
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "llm_enabled": bool(LLM_BASE_URL),
        "llm_model": LLM_MODEL if LLM_BASE_URL else None,
        "web_search_enabled": WEB_SEARCH_ENABLED,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "DuckBill AI Service"
    }), 200 if model_loaded else 503

@app.route('/categories', methods=['GET'])
def get_categories():
    """Retorna as categorias disponíveis"""
    return jsonify({
        "categories": CATEGORIAS_CONHECIDAS,
        "total": len(CATEGORIAS_CONHECIDAS)
    }), 200

@app.route('/model-info', methods=['GET'])
def model_info():
    """Retorna informações sobre o modelo"""
    if not model_loaded:
        return jsonify({"error": "Modelo não carregado"}), 503
    
    try:
        # Obter informações do pipeline
        steps = [step[0] for step in modelo_final.steps] if modelo_final is not None else []
        
        return jsonify({
            "model_type": "Pipeline (TF-IDF + Logistic Regression)",
            "pipeline_steps": steps,
            "categories_count": len(CATEGORIAS_CONHECIDAS),
            "input_format": "text/string",
            "output_format": "category + confidence",
            "training_info": {
                "algorithm": "Logistic Regression",
                "vectorizer": "TF-IDF",
                "class_weight": "balanced",
                "max_iterations": 1000
            }
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter informações do modelo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint de chat financeiro com contexto do usuário"""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({
            "error": "Por favor, envie 'message' no JSON",
            "example": {
                "message": "Quais são meus maiores gastos?",
                "context": {
                    "usuario": {"nome": "Lucas"},
                    "despesas": [],
                    "carteira": [],
                    "metas": [],
                    "categorias": []
                }
            },
            "status": "error"
        }), 400

    mensagem = data.get('message', '')
    mensagem_validada, erro = validar_descricao(mensagem)

    if erro:
        return jsonify({
            "error": erro,
            "status": "error"
        }), 400

    contexto = data.get('context', {})

    try:
        resposta = responder_chat(mensagem_validada, contexto)
        resposta['message'] = mensagem_validada or ""
        resposta['timestamp'] = datetime.utcnow().isoformat()
        return jsonify(resposta), 200
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        return jsonify({
            "error": f"Erro ao processar chat: {str(e)}",
            "status": "error"
        }), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint principal de predição"""
    if not model_loaded:
        return jsonify({
            "error": "Modelo não disponível",
            "status": "error"
        }), 503
    
    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({
            "error": "Por favor, envie 'description' no JSON",
            "example": {"description": "McDonalds Big Mac"},
            "status": "error"
        }), 400
    
    descricao = data.get('description', '')
    
    # Validar entrada
    descricao_validada, erro = validar_descricao(descricao)
    if erro:
        return jsonify({
            "error": erro,
            "status": "error"
        }), 400

    try:
        if modelo_final is None:
            raise RuntimeError("Modelo não carregado")

        # Predição usando o pipeline
        modelo = modelo_final
        texto_predicao = (descricao_validada or "").lower()
        categoria = modelo.predict([texto_predicao])[0]
        probabilidades = modelo.predict_proba([texto_predicao])
        probabilidade_max = probabilidades.max()
        
        # Obter top 3 categorias mais prováveis
        classes = modelo.classes_
        probs = probabilidades[0]
        top_3_indices = probs.argsort()[-3:][::-1]
        top_3_predictions = [
            {
                "category": classes[i],
                "confidence": round(float(probs[i]), 4)
            }
            for i in top_3_indices
        ]

        logger.info(f"Predição realizada: '{descricao_validada}' -> {categoria} ({probabilidade_max:.2%})")

        return jsonify({
            "description": descricao,
            "category": categoria,
            "confidence": round(float(probabilidade_max), 4),
            "top_predictions": top_3_predictions,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        return jsonify({
            "error": f"Erro ao processar predição: {str(e)}",
            "status": "error"
        }), 500

@app.route('/batch-predict', methods=['POST'])
def batch_predict():
    """Endpoint para predição em lote"""
    if not model_loaded:
        return jsonify({
            "error": "Modelo não disponível",
            "status": "error"
        }), 503
    
    data = request.get_json()
    if not data or 'descriptions' not in data:
        return jsonify({
            "error": "Por favor, envie 'descriptions' (array) no JSON",
            "example": {"descriptions": ["McDonalds", "Netflix", "Uber"]},
            "status": "error"
        }), 400
    
    descriptions = data.get('descriptions', [])
    
    if not isinstance(descriptions, list):
        return jsonify({
            "error": "'descriptions' deve ser um array",
            "status": "error"
        }), 400
    
    if len(descriptions) == 0:
        return jsonify({
            "error": "Array 'descriptions' está vazio",
            "status": "error"
        }), 400
    
    if len(descriptions) > 100:
        return jsonify({
            "error": "Máximo de 100 descrições por requisição",
            "status": "error"
        }), 400

    results = []
    errors = []
    
    for idx, desc in enumerate(descriptions):
        desc_validada, erro = validar_descricao(desc)
        
        if erro:
            errors.append({
                "index": idx,
                "description": desc,
                "error": erro
            })
            continue
        
        try:
            if modelo_final is None:
                raise RuntimeError("Modelo não carregado")

            texto_lote = (desc_validada or "").lower()
            categoria = modelo_final.predict([texto_lote])[0]
            probabilidade = modelo_final.predict_proba([texto_lote]).max()
            
            results.append({
                "index": idx,
                "description": desc,
                "category": categoria,
                "confidence": round(float(probabilidade), 4)
            })
        except Exception as e:
            errors.append({
                "index": idx,
                "description": desc,
                "error": str(e)
            })
    
    logger.info(f"Predição em lote: {len(results)} sucessos, {len(errors)} erros")
    
    return jsonify({
        "total_processed": len(descriptions),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors if errors else None,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handler para rotas não encontradas"""
    return jsonify({
        "error": "Endpoint não encontrado",
        "status": "error",
        "available_endpoints": ["/", "/health", "/predict", "/batch-predict", "/model-info", "/categories", "/chat"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "error": "Erro interno do servidor",
        "status": "error"
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') != 'production'
    
    logger.info(f"🚀 Servidor DuckBill IA rodando em http://0.0.0.0:{port}")
    logger.info(f"🔧 Modo: {'Desenvolvimento' if debug else 'Produção'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)