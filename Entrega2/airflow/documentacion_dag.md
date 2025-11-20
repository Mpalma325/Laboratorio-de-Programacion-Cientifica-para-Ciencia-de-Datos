Documentación del DAG.

El DAG predictive_pipeline_xgb implementa un pipeline automatizado de Machine Learning en Airflow. 

Este ejecuta semanalmente una secuencia completa de pasos:  que reentrena el modelo cuando se requiere garantizar trazabilidad mediante MLflow.


A continuación se describe el propósito de cada tarea:

1. prepare_data

Procesa los datos crudos: limpia, transforma y genera los conjuntos necesarios para drift, entrenamiento y predicción.
Es el punto de partida del pipeline, para cada entrada de nuevos datos, se genera una nueva preparación de los datos, por lo que es un paso obligatorio.

2. detect_drift (BranchPythonOperator)

Evalúa si los datos recientes presentan data drift respecto a la distribución histórica, es decir si cambian los promedios de ventas o hay cambios importantes en otros datos.

De detectar drift, se reentrena el modelo, con la finalidad de que el modelo pueda ser representativo a los datos actuales. 

Si es la primera vez que se corre el flujo, también salta a reentrenar el modelo, ya que no hay un modelo anterior y necesita generar un modelo de base.

De no existir drift, se salta directamente el reentrenamiento del modelo.


Así, de manera condicional, se mueve a uno de los dos procesos:

"retrain_xgb" si se detecta drift, "skip_retrain" si no existe drift significativo.

3. retrain_xgb

Entrena un modelo XGBoost únicamente si hubo drift.
Registra métricas, parámetros y artefactos en MLflow.
El modelo entrenado se considera la nueva versión oficial para producción.

4. skip_retrain

Se ejecuta cuando no existe drift.
Funciona como un paso vacío  solamente para mantener el flujo lógico.

5. explain_model

Genera explicaciones del modelo mediante SHAP.
Incluye:

Importancia global de features

Valores SHAP individuales

Gráficos o artefactos interpretables
Se ejecuta solo cuando hay reentrenamiento previo, por lo tanto es un modúlo que sigue directamente a "retrain_xgb".

6. predict_next_week

Genera predicciones usando el modelo más reciente para los datos recientemente añadidos.

Este se  ejecuta independientemente del camino tomado (entrenar o no entrenar), siempre que al menos una de las rutas haya finalizado exitosamente.

Diagrama de flujo del pipeline:


En la siguiente imagen se observa el funcionamiento del Flujo anteriormente mencionado en el siguiente diagrama 
prepare_data → detect_drift → skip_retrain → predict_next_week
                       ↘ retrain_xgb → explain_model ↗