FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
<<<<<<< HEAD
    BACKEND_URL=http://recsys-backend:8001 \
=======
    BACKEND_URL=http://recsys-backend:8100 \
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
    PORT=7861

WORKDIR /app

<<<<<<< HEAD
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
=======
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b

COPY app.py /app/app.py

EXPOSE 7861
<<<<<<< HEAD

CMD ["python", "app.py"]
=======
CMD ["python", "app.py"]
>>>>>>> ef13916040562e15918fd194ff3221eedc59ca1b
