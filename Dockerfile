FROM apache/airflow:2.7.2-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential git curl libssl-dev libffi-dev libpq-dev \
    libsasl2-dev libldap2-dev python3-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy and install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copy entire project
COPY . /opt/airflow

