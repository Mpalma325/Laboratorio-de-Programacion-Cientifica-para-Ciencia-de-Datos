#!/bin/bash
set -e  

echo "Iniciando entorno completo de SodAI Drinks..."

echo "Verificando Docker y docker-compose..."
if ! command -v docker &> /dev/null; then
  echo " Docker no está instalado."; exit 1
fi
if ! command -v docker compose &> /dev/null; then
  echo "Docker compose no está disponible "; exit 1
fi

echo "Levantando Airflow "
cd airflow
docker compose up --build -d
echo "http://localhost:8080 para verificar el DAG."
echo " DAG: predictive_pipeline_xgb"
cd ..

echo "Levantando app"
cd app
docker compose up --build -d
cd ..
echo "App disponible en:"
echo "   - Backend: http://localhost:8000/docs"
echo "   - Frontend: http://localhost:7860"


echo "Levantando Sistema de Recomendación (Bonus)..."
cd bonus/recsys
docker compose up --build -d
cd ../..

echo "Recsys disponible en:"
echo "   - Backend: http://localhost:8100/health"
echo "   - Frontend: http://localhost:7861"


echo "Levantando Chatbot (Bonus)..."
cd bonus/llm
docker compose up --build -d
cd ../..

echo " Chatbot disponible en:"
echo "   - Backend: http://localhost:8200/health"
echo "   - Frontend: http://localhost:7862"

echo ""
echo "TODO listo. Para probar:"
echo "  🔹 Airflow UI → http://localhost:8080"
echo "  🔹 App principal → http://localhost:7860"
echo "  🔹 Recsys bonus → http://localhost:7861"
echo "  🔹 Chatbot bonus → http://localhost:7862"
echo ""
echo "Para bajar todo:"
echo "docker compose down --volumes --remove-orphans"
