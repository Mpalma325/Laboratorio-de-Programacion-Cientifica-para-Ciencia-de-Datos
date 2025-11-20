#!/bin/bash
set -e  

echo "🚀 Iniciando entorno completo de SodAI Drinks..."
echo ""

# Verificar Docker
echo "🔍 Verificando Docker y docker-compose..."
if ! command -v docker &> /dev/null; then
  echo "❌ Docker no está instalado."; exit 1
fi
if ! command -v docker compose &> /dev/null; then
  echo "❌ Docker compose no está disponible"; exit 1
fi
echo "✅ Docker verificado"
echo ""

# Levantar Airflow
echo "📊 Levantando Airflow..."
cd airflow
docker compose up --build -d
echo "✅ Airflow levantado"
echo "   🌐 UI: http://localhost:8080"
echo "   📋 DAG: predictive_pipeline_xgb"
echo "   👤 Usuario: admin / Contraseña: admin"
cd ..
echo ""

# Esperar que Airflow esté listo
echo "⏳ Esperando que Airflow esté listo..."
sleep 10

# Levantar App principal
echo "🎯 Levantando App principal..."
cd app
docker compose up --build -d
echo "✅ App principal levantada"
echo "   🔧 Backend: http://localhost:8000/docs"
echo "   🎨 Frontend: http://localhost:7860"
cd ..
echo ""

# Esperar que App esté lista
echo "⏳ Esperando que App esté lista..."
sleep 5

# Levantar servicios Bonus
echo "🎁 Levantando servicios Bonus..."
cd bonus
docker compose up --build -d
echo "✅ Servicios Bonus levantados"
echo ""
echo "   📚 Sistema de Recomendación (RecSys):"
echo "      🔧 Backend: http://localhost:8001/health"
echo "      🎨 Frontend: http://localhost:7861"
echo ""
echo "   💬 Chatbot Conversacional (LLM):"
echo "      🔧 Backend: http://localhost:8002/health"
echo "      🎨 Frontend: http://localhost:7862"
cd ..
echo ""

# Resumen final
echo "════════════════════════════════════════════════════"
echo "✅ TODO LISTO - Sistema SodAI Drinks en ejecución"
echo "════════════════════════════════════════════════════"
echo ""
echo "📊 AIRFLOW (Pipeline de datos)"
echo "   → http://localhost:8080"
echo "   Usuario: admin / Contraseña: admin"
echo ""
echo "🎯 APP PRINCIPAL (Predicciones)"
echo "   → Frontend: http://localhost:7860"
echo "   → Backend API: http://localhost:8000/docs"
echo ""
echo "🎁 BONUS - Sistema de Recomendación"
echo "   → Frontend: http://localhost:7861"
echo "   → Backend: http://localhost:8001"
echo ""
echo "🎁 BONUS - Chatbot Conversacional"
echo "   → Frontend: http://localhost:7862"
echo "   → Backend: http://localhost:8002"
echo ""
echo "════════════════════════════════════════════════════"
echo ""
echo "🛑 Para detener todos los servicios:"
echo "   ./stop_all.sh"
echo ""
echo "🔄 Para reiniciar todo:"
echo "   ./restart_all.sh"
echo ""
echo "📝 Para ver logs:"
echo "   docker compose logs -f [nombre-servicio]"
echo ""