FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
<<<<<<< HEAD
    BACKEND_URL=http://llm-backend:8002 \
    PORT=7862 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7862

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py

# Asegurar permisos
RUN chmod +x /app/app.py

EXPOSE 7862

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7862/ || exit 1

CMD ["python", "-u", "app.py"]
=======
    BACKEND_URL=http://llm-backend:8200 \
    PORT=7862

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py

EXPOSE 7862
CMD ["python", "app.py"]
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
