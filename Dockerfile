FROM apache/airflow:2.7.2

USER root

# Install OpenJDK-11
RUN apt update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get install -y ant && \
    apt-get install -y --no-install-recommends \
         gcc \
         heimdal-dev  && \
    apt-get clean;

# Set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

USER airflow

COPY requirements.txt /opt

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /opt/requirements.txt
