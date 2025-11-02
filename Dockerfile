
FROM python:3.10-slim

ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.10
ARG CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8080

RUN useradd -ms /bin/bash airflow && \
    mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins && \
    chown -R airflow:airflow ${AIRFLOW_HOME}

COPY dags/ ${AIRFLOW_HOME}/dags/

EXPOSE 8080 7860

RUN mkdir -p /home/airflow/.cache/huggingface/gradio/frpc && \
    curl -L -o /home/airflow/.cache/huggingface/gradio/frpc/frpc_linux_amd64_v0.3 \
        https://cdn-media.huggingface.co/frpc-gradio-0.3/frpc_linux_amd64 && \
    chmod +x /home/airflow/.cache/huggingface/gradio/frpc/frpc_linux_amd64_v0.3 && \
    chown -R airflow:airflow /home/airflow/.cache

USER airflow

CMD bash -lc "\
  airflow db init && \
  airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || true && \
  airflow scheduler & \
  airflow webserver --host 0.0.0.0 \
"
