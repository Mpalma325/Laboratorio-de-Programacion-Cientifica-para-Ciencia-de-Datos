FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_URL=http://backend:8000 \
    PORT=7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
<<<<<<< HEAD
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
=======
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b

COPY app.py /app/app.py

EXPOSE 7860

<<<<<<< HEAD
CMD ["python", "app.py"]
=======
CMD ["python", "app.py"]
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
