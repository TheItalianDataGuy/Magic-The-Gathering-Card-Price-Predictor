FROM python:3.11-slim

# --- 1. Install system dependencies ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential git curl libssl-dev libffi-dev libpq-dev \
    libsasl2-dev libldap2-dev python3-dev libkrb5-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# --- 2. Set environment variables ---
ENV AIRFLOW_VERSION=2.7.2
ENV AIRFLOW_HOME=/opt/airflow
ENV PATH="/home/airflow/.local/bin:/usr/local/bin:$PATH"
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False

# --- 3. Create airflow user and necessary directories ---
RUN useradd -ms /bin/bash airflow && \
    mkdir -p $AIRFLOW_HOME/dags $AIRFLOW_HOME/logs $AIRFLOW_HOME/plugins $AIRFLOW_HOME/data/raw && \
    chown -R airflow: $AIRFLOW_HOME

# --- 4. Install Airflow and Python dependencies as root ---
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install apache-airflow==${AIRFLOW_VERSION} && \
    pip install -r /tmp/requirements.txt

# --- 5. Switch to airflow user ---
USER airflow
WORKDIR $AIRFLOW_HOME

# --- 6. Copy the project code and set ownership ---
COPY --chown=airflow:airflow . $AIRFLOW_HOME

# --- 7. Default command (can be overridden in docker-compose) ---
CMD ["airflow", "webserver"]
