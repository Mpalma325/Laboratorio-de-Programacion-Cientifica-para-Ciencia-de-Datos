Proyecto MLOps + App + LLM + Recsys

## Descripción General

Este proyecto implementa un sistema completo que combina MLOps, aplicaciones web, un chat basado en lenguaje natural y un sistema de recomendación. El objetivo es integrar un pipeline de Machine Learning supervisado por Airflow, junto con herramientas que permiten interactuar con los datos y generar recomendaciones personalizadas.

El sistema completo incluye:

* Un pipeline predictivo con Airflow y MLflow
* Una aplicación principal con backend y frontend, para consultar estado de los datos, y consultar predicciones.
* Un chat LLM para explorar y consultar información del dataset de transacciones
* Un sistema de recomendación por usuario y semana

Todo está contenedorizado con Docker para facilitar la ejecución.

---

## Arquitectura General del Proyecto

El proyecto está dividido en tres módulos principales:

1. *Airflow*: contiene el pipeline de Machine Learning, el flujo de datos, la detección de drift, el reentrenamiento condicional, la generación de explicaciones y la predicción semanal.
2. *App principal*: una aplicación con backend (FastAPI) y frontend (Gradio) que permite subir archivos, interactuar con el sistema y visualizar resultados.
3. *Bonus*: dos aplicaciones adicionales:

   * Un chat LLM que permite hacer preguntas sobre los datos de transacciones usando lenguaje natural.
   * Un sistema de recomendación basado en historial de usuarios y semanas específicas.

---

## Estructura del Proyecto

* *airflow*: contiene el DAG, los scripts de cada etapa del pipeline, MLflow para versionamiento de modelos, y los contenedores necesarios para orquestación.
* *app*:

  * backend: API desarrollada con FastAPI.
  * frontend: interfaz interactiva construida con Gradio.
* *bonus*:

  * llm: chat inteligente para consultar datos.
  * recsys: sistema de recomendación por usuario y semana.


## Pipeline de Airflow

El pipeline implementa un flujo semanal que:

1. Prepara los datos.
2. Detecta si hay drift respecto al histórico.
3. Reentrena el modelo solo si es necesario.
4. Genera explicaciones del modelo con SHAP.
5. Produce predicciones para la semana siguiente.

## Aplicación Principal (Backend y Frontend)

La aplicación principal permite:

* Visualizar resultados.
* Revisar estados del sistema.

El backend maneja la lógica y las APIs, mientras que el frontend ofrece una interfaz simple para los usuarios.

## Chatbot (Bonus)


* Consultar información del dataset de transacciones mediante lenguaje natural.

## Sistema de Recomendación (Bonus)

Genera recomendaciones personalizadas considerando:

* Historial de compras por usuario.
* Semana específica del año.
* Productos similares o complementarios.



## Tecnologías Utilizadas

* Apache Airflow
* MLflow
* XGBoost
* FastAPI
* Gradio
* Docker y Docker Compose
* Pandas y NumPy
* SHAP
* Modelos LLM (según implementación en bonus)


## Ejecución del Sistema

Cada módulo tiene su propio archivo docker-compose. Se pueden ejecutar de forma independiente, el pipeline es actualizado de manera semanal, y se agregan nuevos datos en la carpeta data/raw, donde se subirían los nuevos datos semanales.

* Airflow: dentro de la carpeta airflow.
* Aplicación principal: dentro de la carpeta app.
* Chat LLM: dentro de bonus/llm.
* Recsys: dentro de bonus/recsys.


Si se quieren utilizar de manera conjunta, o que corran todos los módulos a la vez, se puede usar el archivo run all, con los siguientes comandos a utilizar, todos estos en la terminal de git bash:


Levantar el sistema (Todos los contenedores): ./run_all.sh

Detener el sistema: ./stop_all.sh



Es muy importante el uso de RAM para este proyecto (en conclusiones se observa un comentario muy importante al respecto), por lo que se requiere un computador con buena memoria RAM para poder correr los DAGs de manera exitosa.

## Resultados

El sistema completo permite:

* Automatizar un pipeline ML con reentrenamiento inteligente.
* Consultar datos mediante un asistente de lenguaje natural.
* Obtener recomendaciones personalizadas semanales.
* Interactuar con los datos mediante una interfaz amigable.
* Llevar trazabilidad completa del modelo con MLflow.
