FROM apache/airflow:2.8.1

USER root

# Install OpenJDK-17 (The 'muscle' Spark needs)
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME correctly for the container environment
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

USER airflow

# Install the required Python providers and libraries
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark \
    requests \
    faker \
    psycopg2-binary \
    pandas \
    sqlalchemy