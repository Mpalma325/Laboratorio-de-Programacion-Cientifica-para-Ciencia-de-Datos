FROM python:3.11-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app.py .

# Exponer puerto
EXPOSE 7861

# Comando de inicio
CMD ["python", "app.py"]