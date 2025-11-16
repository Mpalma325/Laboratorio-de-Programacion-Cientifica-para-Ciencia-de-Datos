@echo off
setlocal enabledelayedexpansion

REM ================================================
REM  SodAI Drinks - Runner para Windows (CMD)
REM  Uso:
REM    run_all.bat all         -> levanta todo (airflow, app, recsys, llm)
REM    run_all.bat airflow     -> solo Airflow
REM    run_all.bat app         -> solo App (backend+frontend)
REM    run_all.bat recsys      -> solo Bonus Recsys
REM    run_all.bat llm         -> solo Bonus LLM
REM    run_all.bat down        -> baja todo (en todas las carpetas)
REM ================================================

IF "%~1"=="" GOTO :help

REM ---- Verificar Docker ----
where docker >nul 2>nul
IF ERRORLEVEL 1 (
  echo [ERROR] Docker no esta instalado o no esta en PATH.
  exit /b 1
)

REM ---- Detectar docker compose (plugin vs binario) ----
docker compose version >nul 2>nul
IF ERRORLEVEL 0 (
  set "DOCKER_COMPOSE_CMD=docker compose"
) ELSE (
  where docker-compose >nul 2>nul
  IF ERRORLEVEL 0 (
    set "DOCKER_COMPOSE_CMD=docker-compose"
  ) ELSE (
    echo [ERROR] No se encontro 'docker compose' ni 'docker-compose'.
    echo Instala Docker Desktop o el plugin de compose.
    exit /b 1
  )
)

REM ---- Enrutador ----
IF /I "%~1"=="all"    GOTO :all
IF /I "%~1"=="airflow" GOTO :airflow
IF /I "%~1"=="app"     GOTO :app
IF /I "%~1"=="recsys"  GOTO :recsys
IF /I "%~1"=="llm"     GOTO :llm
IF /I "%~1"=="down"    GOTO :down

GOTO :help

:airflow
  echo.
  echo === Levantando Airflow (pipeline productivo) ===
  pushd airflow
  %DOCKER_COMPOSE_CMD% up --build -d
  popd
  echo Airflow UI: http://localhost:8080
  echo Espera unos segundos a que arranque el webserver...
  goto :eof

:app
  echo.
  echo === Levantando App principal (backend + frontend) ===
  REM Aviso por si faltan predicciones:
  IF NOT EXIST "airflow\data\predictions" (
    echo [AVISO] No existe carpeta airflow\data\predictions. El backend puede no encontrar .parquet.
  )
  pushd app
  %DOCKER_COMPOSE_CMD% up --build -d
  popd
  echo Backend:  http://localhost:8000/docs
  echo Frontend: http://localhost:7860
  goto :eof

:recsys
  echo.
  echo === Levantando Bonus: Recsys (backend + frontend) ===
  IF NOT EXIST "airflow\data\raw" (
    echo [AVISO] No existe carpeta airflow\data\raw. El recsys necesita transacciones.parquet.
  )
  pushd bonus\recsys
  %DOCKER_COMPOSE_CMD% up --build -d
  popd
  echo Recsys Backend:  http://localhost:8100/health
  echo Recsys Frontend: http://localhost:7861
  goto :eof

:llm
  echo.
  echo === Levantando Bonus: LLM (backend + frontend) ===
  IF NOT EXIST "airflow\data\raw" (
    echo [AVISO] No existe carpeta airflow\data\raw. El chatbot leera clientes/productos/transacciones.parquet.
  )
  pushd bonus\llm
  %DOCKER_COMPOSE_CMD% up --build -d
  popd
  echo LLM Backend:  http://localhost:8200/health
  echo LLM Frontend: http://localhost:7862
  goto :eof

:all
  call "%~f0" airflow
  call "%~f0" app
  call "%~f0" recsys
  call "%~f0" llm
  echo.
  echo ==== Todo levantado ====
  echo Airflow:        http://localhost:8080
  echo App Frontend:   http://localhost:7860
  echo Recsys:         http://localhost:7861
  echo LLM:            http://localhost:7862
  goto :eof

:down
  echo.
  echo === Bajando todos los servicios (con --volumes y --remove-orphans) ===
  if exist airflow (
    pushd airflow
    %DOCKER_COMPOSE_CMD% down --volumes --remove-orphans
    popd
  )
  if exist app (
    pushd app
    %DOCKER_COMPOSE_CMD% down --volumes --remove-orphans
    popd
  )
  if exist bonus\recsys (
    pushd bonus\recsys
    %DOCKER_COMPOSE_CMD% down --volumes --remove-orphans
    popd
  )
  if exist bonus\llm (
    pushd bonus\llm
    %DOCKER_COMPOSE_CMD% down --volumes --remove-orphans
    popd
  )
  echo Listo. Todo abajo.
  goto :eof

:help
  echo.
  echo Uso:
  echo   run_all.bat all       ^(levanta todo^)
  echo   run_all.bat airflow   ^(solo Airflow^)
  echo   run_all.bat app       ^(solo App principal^)
  echo   run_all.bat recsys    ^(solo Bonus Recsys^)
  echo   run_all.bat llm       ^(solo Bonus LLM^)
  echo   run_all.bat down      ^(baja todo^)
  exit /b 0
