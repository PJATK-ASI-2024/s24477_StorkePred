import pymsteams
import os

def notify_failure(context):
    if not os.getenv("MSTEAMS_WEBHOOK_URL"):
        raise ValueError("MSTEAMS_WEBHOOK_URL is not set")

    # Create a connector for the team
    teams_failure_message = pymsteams.connectorcard(os.getenv("MSTEAMS_WEBHOOK_URL"))

    # Create the message with the name of the failed DAG and failed task
    teams_failure_message.title("Airflow DAG Failed")
    teams_failure_message.text(
        f"DAG: {context['task_instance'].dag_id} \n Task: {context['task_instance'].task_id} \n [Check run for more details](http://localhost:8080/dags/create_model/grid?tab=graph&dag_run_id={context['run_id']})"
    )

    teams_failure_message.color("ff0000")

    # Send the message
    teams_failure_message.send()


def notify_success(context):
    if not os.getenv("MSTEAMS_WEBHOOK_URL"):
        raise ValueError("MSTEAMS_WEBHOOK_URL is not set")

    teams_success_message = pymsteams.connectorcard(os.getenv("MSTEAMS_WEBHOOK_URL"))

    teams_success_message.title("Airflow DAG Succeeded")
    teams_success_message.text(
        f"DAG: {context['task_instance'].dag_id} \n Task: {context['task_instance'].task_id}"
    )
    teams_success_message.color("00ff00")

    teams_success_message.send()
