Conclusiones

El desarrollo de esta entrega permitió experimentar de forma práctica los principios fundamentales de un flujo MLOps moderno: orquestación, reproductibilidad, trazabilidad, monitoreo y despliegue. A lo largo del trabajo fueron apareciendo desafíos técnicos y decisiones de diseño que enriquecieron la comprensión de cómo llevar un modelo de machine learning desde experimentos locales hasta un sistema funcional y mantenible.

Uso de herramientas de tracking y despliegue

La integración de MLflow marcó una diferencia significativa en la forma de trabajar con el modelo. Poder registrar hiperparámetros, métricas, artefactos y versiones del modelo facilitó el debugging, permitió comparar configuraciones y entregó transparencia en la evolución del sistema. En vez de depender de archivos dispersos, el tracking centralizado favoreció un flujo mucho más ordenado y permitió reentrenar el modelo sin perder trazabilidad.

El despliegue mediante contenedores Docker también simplificó la portabilidad del sistema: tanto el backend como el frontend pueden ejecutarse en cualquier entorno sin depender de configuraciones externas. Esto acercó el proyecto a un escenario más realista de producción.

Desafíos del despliegue con FastAPI y Gradio

Una de las partes más interesantes fue la integración entre FastAPI y Gradio, ya que permitió crear un flujo completo desde la generación de predicciones hasta la interacción del usuario final. El backend planteó desafíos relacionados con el manejo robusto de errores, la estandarización de los datos de entrada y la lectura correcta de artefactos generados por el pipeline. Por su parte, Gradio ofreció una interfaz simple pero intuitiva; sin embargo, fue necesario diseñar cuidadosamente la comunicación entre ambos servicios y las variables de entorno en Docker para asegurar que los contenedores se encontraran correctamente.

Este enfoque doble (API + interfaz) permitió visualizar cómo un modelo no sólo funciona, sino también cómo un usuario real lo utilizaría.

Aporte de Airflow a la robustez y escalabilidad

El uso de Apache Airflow fue clave para transformar un conjunto de scripts sueltos en un pipeline reproducible y escalable. La orquestación basada en DAGs permitió:

Estructurar el ciclo completo de datos → features → entrenamiento → interpretabilidad → predicciones.

Gestionar dependencias entre tareas y evitar ejecuciones inconsistentes.

Integrar etapas adicionales como la detección de drift y el reentrenamiento condicional.

Facilitar la inclusión de nuevos datos y versiones posteriores del modelo sin necesidad de rehacer manualmente el flujo.

Airflow aporta una visión mucho más cercana a entornos de producción, donde la automatización y la calidad del pipeline son tan importantes como el modelo mismo.

Oportunidades de mejora y extensiones futuras

Aunque el sistema funciona de punta a punta, existen varias oportunidades para enriquecerlo en una futura iteración:

Automatizar aún más el monitoreo, integrando alertas cuando el pipeline falle, cuando el drift supere cierto umbral o cuando el rendimiento del modelo decaiga.

Agregar métricas de servicio, como latencia de predicción, tasa de errores del backend o trazabilidad por usuario.

Incorporar validaciones de datos robustas usando herramientas como Great Expectations u otros enfoques de Data Quality.

Versionar datasets, no solo modelos, para tener histórico completo del proceso.

Escalar a un ambiente más realista con despliegue en la nube, almacenamiento distribuido y orquestación mediante contenedores en Kubernetes.

Optimizar el sistema de recomendaciones o integrar modelos adicionales en el bonus, permitiendo un flujo multi-modelo más complejo.

En general, el proyecto permitió comprender no solo cómo entrenar un modelo, sino cómo diseñar un sistema completo capaz de operar de forma confiable, auditable y extensible. La experiencia dejó claro que en MLOps, el código del modelo es sólo una parte: lo realmente importante es todo lo que lo rodea.