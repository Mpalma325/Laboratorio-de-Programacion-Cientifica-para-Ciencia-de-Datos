@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo 🚀 Iniciando entorno completo de SodAI Drinks...
echo ========================================================
echo.

REM Verificar Docker
echo 🔍 Verificando Docker y docker-compose...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está instalado o no está en el PATH
    pause
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose no está disponible
    pause
    exit /b 1
)
echo ✅ Docker verificado
echo.

REM Levantar Airflow
echo ========================================================
echo 📊 Levantando Airflow...
echo ========================================================
cd airflow
docker compose up --build -d
if errorlevel 1 (
    echo ❌ Error al levantar Airflow
    cd ..
    pause
    exit /b 1
)
echo ✅ Airflow levantado
echo    🌐 UI: http://localhost:8080
echo    📋 DAG: predictive_pipeline_xgb
echo    👤 Usuario: admin / Contraseña: admin
cd ..
echo.

REM Esperar que Airflow esté listo
echo ⏳ Esperando que Airflow esté listo...
timeout /t 10 /nobreak >nul
echo.

REM Levantar App principal
echo ========================================================
echo 🎯 Levantando App principal...
echo ========================================================
cd app
docker compose up --build -d
if errorlevel 1 (
    echo ❌ Error al levantar App
    cd ..
    pause
    exit /b 1
)
echo ✅ App principal levantada
echo    🔧 Backend: http://localhost:8000/docs
echo    🎨 Frontend: http://localhost:7860
cd ..
echo.

REM Esperar que App esté lista
echo ⏳ Esperando que App esté lista...
timeout /t 5 /nobreak >nul
echo.

REM Levantar servicios Bonus
echo ========================================================
echo 🎁 Levantando servicios Bonus...
echo ========================================================
cd bonus
docker compose up --build -d
if errorlevel 1 (
    echo ❌ Error al levantar servicios Bonus
    cd ..
    pause
    exit /b 1
)
echo ✅ Servicios Bonus levantados
echo.
echo    📚 Sistema de Recomendación (RecSys):
echo       🔧 Backend: http://localhost:8001/health
echo       🎨 Frontend: http://localhost:7861
echo.
echo    💬 Chatbot Conversacional (LLM):
echo       🔧 Backend: http://localhost:8002/health
echo       🎨 Frontend: http://localhost:7862
cd ..
echo.

REM Resumen final
echo ========================================================
echo ✅ TODO LISTO - Sistema SodAI Drinks en ejecución
echo ========================================================
echo.
echo 📊 AIRFLOW (Pipeline de datos)
echo    → http://localhost:8080
echo    Usuario: admin / Contraseña: admin
echo.
echo 🎯 APP PRINCIPAL (Predicciones)
echo    → Frontend: http://localhost:7860
echo    → Backend API: http://localhost:8000/docs
echo.
echo 🎁 BONUS - Sistema de Recomendación
echo    → Frontend: http://localhost:7861
echo    → Backend: http://localhost:8001
echo.
echo 🎁 BONUS - Chatbot Conversacional
echo    → Frontend: http://localhost:7862
echo    → Backend: http://localhost:8002
echo.
echo ========================================================
echo.
echo 🛑 Para detener todos los servicios: stop_all.bat
echo 🔄 Para reiniciar todo: restart_all.bat
echo 📊 Para ver estado: check_status.bat
echo.
echo ========================================================
pause