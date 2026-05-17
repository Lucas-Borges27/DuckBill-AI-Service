FROM python:3.11-slim

WORKDIR /app

# Build context must be DuckBill-AI-Service/ root (see docker-compose.yml)
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/appClassificacao.py .
COPY src/modelo_categorizador_bancario.pkl .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "appClassificacao:app"]
