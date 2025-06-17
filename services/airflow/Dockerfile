# Airflow Service Dockerfile
FROM apache/airflow:2.7.3-python3.10

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Copy DAGs
COPY dags/ /opt/airflow/dags/

# Set timezone to Asia/Jakarta
ENV TZ=Asia/Jakarta
