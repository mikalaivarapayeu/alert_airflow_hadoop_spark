import datetime
import glob
from airflow.decorators import dag, task
from airflow.operators.email import EmailOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
from scripts. copying_file_to_HDFS import copy_to_hdfs
from airflow.models import Variable


@dag(start_date=datetime.datetime(2021, 1, 1), schedule="@once", max_active_runs=1, catchup=False)
def alert_spark_airflow():
    @task.branch(task_id="if_log_data_exist")
    def if_log_data_exist():
        if len(glob.glob("/opt/mnt/data/*.csv")) > 0:
            return ['copy_log_file_to_hdfs']

    copy_log_file_to_hdfs = PythonOperator(
        task_id="copy_log_file_to_hdfs",
        python_callable=copy_to_hdfs
    )
    spark_log_processing = SparkSubmitOperator(
        task_id="spark_log_processing",
        application="/opt/spark/app/alert_spark.py",
        conn_id="spark_conn",
        verbose=False
    )

    @task.branch(task_id="if_error_count_files_exist")
    def if_error_count_files_exist():
        if len(glob.glob("/opt/mnt/unprocessed_alert/*.csv")) > 0:
            return ['sending_email_notification']
        return ['move_data_log_files']

    sending_email_notification = EmailOperator(

        task_id="sending_email_notification",
        to=Variable.get("email_dest"),
        subject="alert notifications",
        params={'file_name_list': glob.glob("/opt/mnt/unprocessed_alert/*.csv")},
        html_content="<h3>Alert notification</h3>"
                     "<p>Please check the following files in /alert/mnt/processed_alert folder</p>"
                     "<ul>"
                     "{% for file in params.file_name_list %} <li>{{ file.split('/')[-1] }};</li>{%endfor %}"
                     "</ul>"
                     "<br>"
                     "<p>AIRFLOW ALERT SUPPORT TEAM</p>",
        trigger_rule='all_success'

    )

    move_error_calculated_files = BashOperator(

        task_id="move_error_calculated_files",
        bash_command="mv /opt/mnt/unprocessed_alert/*.csv  /opt/mnt/processed_alert",
        trigger_rule='all_success'

    )

    move_data_log_files = BashOperator(

        task_id="move_data_log_files",
        bash_command="mv /opt/mnt/data/*.csv  /opt/mnt/processed_logs",
        trigger_rule='none_failed_min_one_success'
    )

    if_log_data_exist() >> copy_log_file_to_hdfs >> spark_log_processing >> if_error_count_files_exist() >> (sending_email_notification, move_data_log_files)
    sending_email_notification >> move_error_calculated_files >> move_data_log_files


alert_spark_airflow()
