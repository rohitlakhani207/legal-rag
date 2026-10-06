# Backend API image (FastAPI + fastembed ONNX models, CPU only).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MODEL_CACHE_DIR=/models

RUN useradd --create-home --uid 1000 app && mkdir -p /models /app/evaluation/results && chown -R app /models /app

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY --chown=app backend/app backend/app
COPY --chown=app data/sources.json data/sources.json
COPY --chown=app data/corpus data/corpus
COPY --chown=app evaluation/questions.json evaluation/questions.json

USER app
WORKDIR /app/backend

# Bake the embedding and reranker models into the image so the stack works offline after
# the build. Override with --build-arg EMBEDDING_MODEL=... / RERANKER_MODEL=... if you change them.
ARG PRELOAD_MODELS=true
ARG EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
ARG RERANKER_MODEL=Xenova/ms-marco-MiniLM-L-12-v2
RUN if [ "$PRELOAD_MODELS" = "true" ]; then \
      python -c "from fastembed import TextEmbedding; from fastembed.rerank.cross_encoder import TextCrossEncoder; \
TextEmbedding('$EMBEDDING_MODEL', cache_dir='/models'); TextCrossEncoder('$RERANKER_MODEL', cache_dir='/models')"; \
    fi

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
