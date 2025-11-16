#!/bin/bash
set -e  # Detiene si hay error

echo "🚀 Iniciando entorno completo de SodAI Drinks..."

# 1️⃣ Verificar dependencias
echo "🧰 Verificando Docker y docker-compose..."
if ! command -v docker &> /dev/null; then
  echo "❌ Docker no está instalado. Instálalo antes de continuar."; exit 1
fi
if ! command -v docker compose &> /dev/null; then
  echo "❌ docker compose no está disponible (usa Docker Desktop o instala plugin)."; exit 1
fi

# 2️⃣ Levantar Airflow (pipeline productivo)
echo "📦 Levantando Airflow (pipeline productivo)..."
cd airflow
docker compose up --build -d
echo "⏳ Espera 60s y luego entra a http://localhost:8080 para verificar el DAG."
echo "👉 DAG: predictive_pipeline_xgb"
cd ..

# 3️⃣ Levantar aplicación principal (FastAPI + Gradio)
echo "🌐 Levantando aplicación principal (backend + frontend)..."
cd app
docker compose up --build -d
cd ..
echo "✅ App disponible en:"
echo "   - Backend: http://localhost:8000/docs"
echo "   - Frontend: http://localhost:7860"

# 4️⃣ Levantar Bonus: Sistema de Recomendación
echo "🧠 Levantando Sistema de Recomendación (Bonus)..."
cd bonus/recsys
docker compose up --build -d
cd ../..

echo "✅ Recsys disponible en:"
echo "   - Backend: http://localhost:8100/health"
echo "   - Frontend: http://localhost:7861"

# 5️⃣ Levantar Bonus: Chatbot
echo "💬 Levantando Chatbot (Bonus)..."
cd bonus/llm
docker compose up --build -d
cd ../..

echo "✅ Chatbot disponible en:"
echo "   - Backend: http://localhost:8200/health"
echo "   - Frontend: http://localhost:7862"

echo ""
echo "🎉 TODO listo. Puedes probar:"
echo "  🔹 Airflow UI → http://localhost:8080"
echo "  🔹 App principal → http://localhost:7860"
echo "  🔹 Recsys bonus → http://localhost:7861"
echo "  🔹 Chatbot bonus → http://localhost:7862"
echo ""
echo "Cuando termines, puedes bajar todo con:"
echo "docker compose down --volumes --remove-orphans"
