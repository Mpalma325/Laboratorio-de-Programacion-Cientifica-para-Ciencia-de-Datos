#!/bin/bash
set -e

echo "🛑 Deteniendo todos los servicios de SodAI Drinks..."
echo ""

# Detener Bonus
echo "📦 Deteniendo servicios Bonus..."
cd bonus
docker compose down --volumes --remove-orphans
cd ..
echo "✅ Bonus detenido"
echo ""

# Detener App
echo "📦 Deteniendo App principal..."
cd app
docker compose down --volumes --remove-orphans
cd ..
echo "✅ App detenida"
echo ""

# Detener Airflow
echo "📦 Deteniendo Airflow..."
cd airflow
docker compose down --volumes --remove-orphans
cd ..
echo "✅ Airflow detenido"
echo ""

echo "════════════════════════════════════════════════════"
echo "✅ Todos los servicios han sido detenidos"
echo "════════════════════════════════════════════════════"