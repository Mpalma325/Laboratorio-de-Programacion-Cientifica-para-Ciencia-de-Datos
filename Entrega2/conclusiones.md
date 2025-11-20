Conclusiones:

El desarrollo de esta entrega permitió evidenciar los principios esenciales de un flujo MLOps moderno: orquestación, reproducibilidad, trazabilidad, monitoreo y despliegue. Estos componentes hacen posible llevar un modelo ML desde experimentos locales hasta un sistema funcional y mantenible. Así, no solo se profundizó en el entrenamiento de un modelo, sino en el diseño de un ecosistema completo, capaz de operar de manera confiable, auditable y extensible. Con ello queda claro que, en MLOps, el código del modelo es solo una parte; el verdadero valor radica en toda la infraestructura y procesos que lo soportan.

Uso de herramientas de tracking y despliegue:

La integración de MLflow marcó una diferencia significativa en la forma de trabajar con el modelo. En vez de depender de archivos dispersos, el tracking centralizado favoreció un flujo mucho más ordenado y permitió reentrenar el modelo sin perder trazabilidad. Por otro lado, el despliegue mediante contenedores Docker reforzó la portabilidad del sistema. Tanto el backend como el frontend pudieron ejecutarse de forma consistente en cualquier entorno, sin depender de configuraciones locales, acercando este proyecto a un escenario real de producción.

Desafíos del despliegue con FastAPI y Gradio:

La combinación de FastAPI y Gradio permitió implementar un flujo completo: desde la generación de predicciones hasta su consumo por un usuario final. El backend presentó desafíos relacionados con el manejo robusto de errores, la estandarización de los datos de entrada y la lectura correcta de los artefactos generados por el pipeline. Por su parte, Gradio, si bien ofreció una interfaz simple e intuitiva, requirió una configuración cuidadosa para asegurar una comunicación estable entre servicios y un manejo adecuado de variables de entorno dentro de Docker. Este enfoque doble permitió no solo visualizar el funcionamiento del modelo, sino también comprender cómo sería su uso en un escenario real.

Aporte de Airflow a la robustez y escalabilidad:

Airflow permitío transformar un conjunto de scripts sueltos en un pipeline reproducible y escalable. Su modelo basado en DAGs ordenó el ciclo completo del sistema (preparación de datos, ingeniería de features, entrenamiento, interpretabilidad y predicciones), garantizando la correcta gestión de dependencias y evitando ejecuciones inconsistentes. Además, facilitó la incorporación de etapas adicionales como detección de drift y reentrenamiento condicional, permitiendo extender el sistema sin necesidad de reconstruirlo manualmente. En conjunto, Airflow aportó una visión más cercana a entornos productivos, donde la automatización y la calidad del pipeline son tan críticas como el desempeño del propio modelo.

Oportunidades de mejora y extensiones futuras:

- Incorporar validaciones de datos más rigurosas para evaluar qué tan realista es el caso de estudio y cuán cercano está a datos operacionales reales.
- Optimizar el sistema de recomendación o integrar modelos adicionales en el bonus, avanzando hacia un flujo multi-modelo más complejo.
- Mejorar la eficiencia del pipeline, reduciendo tiempos de procesamiento y consumo de memoria, actualmente con una RAM menor a unos 12 GB, no es posible ni siquiera pasar del paso de procesamiento de Data. 
