#!/bin/bash
set -e

echo "🛑 Deteniendo todos los servicios de SodAI Drinks..."
echo ""

echo "📦 Deteniendo servicios Bonus..."
cd bonus
docker compose down --volumes --remove-orphans
cd ..
echo "✅ Bonus detenido"
echo ""

echo "📦 Deteniendo App principal..."
cd app
docker compose down --volumes --remove-orphans
cd ..
echo "✅ App detenida"
echo ""

echo "📦 Deteniendo Airflow..."
cd airflow
docker compose down --volumes --remove-orphans
cd ..
echo "✅ Airflow detenido"
echo ""

echo "════════════════════════════════════════════════════"
echo "✅ Todos los servicios han sido detenidos"
echo "════════════════════════════════════════════════════"