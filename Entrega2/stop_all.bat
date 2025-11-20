@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo 🛑 Deteniendo todos los servicios de SodAI Drinks...
echo ========================================================
echo.

REM Detener Bonus
echo 📦 Deteniendo servicios Bonus...
cd bonus
docker compose down --volumes --remove-orphans
if errorlevel 1 (
    echo ⚠️ Advertencia: Error al detener servicios Bonus
) else (
    echo ✅ Bonus detenido
)
cd ..
echo.

REM Detener App
echo 📦 Deteniendo App principal...
cd app
docker compose down --volumes --remove-orphans
if errorlevel 1 (
    echo ⚠️ Advertencia: Error al detener App
) else (
    echo ✅ App detenida
)
cd ..
echo.

REM Detener Airflow
echo 📦 Deteniendo Airflow...
cd airflow
docker compose down --volumes --remove-orphans
if errorlevel 1 (
    echo ⚠️ Advertencia: Error al detener Airflow
) else (
    echo ✅ Airflow detenido
)
cd ..
echo.

echo ========================================================
echo ✅ Todos los servicios han sido detenidos
echo ========================================================
echo.
pause