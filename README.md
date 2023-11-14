## Alert_spark_hadoop_airflow

### Application description

This application processes log files in the csv format that should be placed into mnt/data folder.
The Airflow detect log files and then invoke a spark application to process them.
If critical errors are detected, new csv files with error count and window over which errors
are written into mnt/unprocessed_alert are written.
Airflow sends emails, and error files are copied into /mnt/processed_alert folder.
Log files are moved into mnt/processed_log folder.

### Installation
- _1. Ensure that docker and docker compose are in stalled_
- _2. Clone the repository_
- _3. In the root folder create the .env file with following environment variables:_
* * _AIRFLOW_UID=1000_
* * _AIRFLOW__CORE__EXECUTOR=CeleryExecutor_
* * _AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow_
* * _AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow_
* * _AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow_
* * _AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/0_
* * _AIRFLOW__CORE__FERNET_KEY=46BKJoQYlPPOexq0OhDZnIlNepKFf87WFwLbfzqDDho=_
* * _AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=true_
* * _AIRFLOW__CORE__LOAD_EXAMPLES=false_
* * _AIRFLOW__API__AUTH_BACKENDS='airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'_
* * _AIRFLOW__SMTP__SMTP_HOST=<'your email/host provider'>_
* * _AIRFLOW__SMTP__SMTP_STARTTL=True_
* * _AIRFLOW__SMTP__SMTP_SSL=False_
* * _AIRFLOW__SMTP__SMTP_USER=<'your email from which sent alerts'>_
* * _AIRFLOW__SMTP__SMTP_PASSWORD=<'your password generated for smtp communication '>_
* * _AIRFLOW__SMTP__SMTP_PORT=587_
* * _AIRFLOW__SMTP__SMTP_MAIL_FROM=<'your email from which sent alerts'>_
* * _AIRFLOW_CONN_ERROR_FOLDER=/opt/mnt_
* * _AIRFLOW_CONN_SPARK_CONN=spark://spark:7077?queue=root.default_
* * _AIRFLOW_CONN_HDFS_CONN=webhdfs://namenode:9000_
* * _AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=true_
* * _AIRFLOW_VAR_EMAIL_DEST=<'email where to sent alerts'>_

Pay attention that for variables with <> one should provide user own values

### Quick start

After creating .env file simply from the alert folder in the terminal run command _**docker compose -f docker-compose.yaml up -d**_