from datetime import datetime

from airflow.decorators import dag, task
from airflow.sensors.external_task import ExternalTaskSensor
import docker


@dag(
    schedule_interval="@once",
    start_date=datetime.now(),
    catchup=False,
    dag_display_name="Build docker image",
)
def build_docker():
    @task()
    def build_docker_image():
        client = docker.from_env()

        client.images.build(
            path="/opt/airflow/Dockerfile", tag="s24477/strokepred:latest", target="api"
        )

        return

    @task()
    def push_docker_image():
        client = docker.from_env()

        client.images.push("s24477/strokepred:latest")
        return

    ets = ExternalTaskSensor(task_id="sensor_for_model", external_dag_id="create_model")
    ets >> build_docker_image() >> push_docker_image()


build_docker()
