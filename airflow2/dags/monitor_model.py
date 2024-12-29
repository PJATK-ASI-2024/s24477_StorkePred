import os
from datetime import datetime

import gspread
import pandas as pd
from airflow.decorators import dag, task
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.email import EmailOperator

from pycaret.classification import load_model

import pymsteams


@dag(
    schedule_interval="@once",
    start_date=datetime.now(),
    catchup=False,
    dag_display_name="Model monitoring",
)
def monitor_model():
    @task()
    def download_evaluation_data():
        gc = gspread.service_account()
        spreadsheet = gc.open(os.getenv("STROKEPRED_SHEET_URL"))
        wks_evaluation = spreadsheet.worksheet("tune")
        evaluation_df = pd.DataFrame(wks_evaluation.get_all_records())
        return evaluation_df

    @task()
    def load_trained_model():
        model = load_model("strokepred_model")
        return model

    @task()
    def evaluate_model(model, evaluation_data):
        predictions = model.predict(evaluation_data)

        # calculate accuracy
        accuracy = (predictions == evaluation_data["prediction_label"]).mean()

        return accuracy

    @task()
    def notify_msteams(acc):
        if acc > 0.8:
            print("Model is performing well!")
            return

        webhook_url = os.getenv("MSTEAMS_WEBHOOK_URL")

        if webhook_url is None:
            print("No webhook URL provided")
            return

        message = pymsteams.connectorcard(webhook_url)
        message.text(f"Model is performing poorly! Accuracy: {acc}")
        message.send()

        return

    evaluation_data = download_evaluation_data()
    model = load_trained_model()

    ets = ExternalTaskSensor(task_id="sensor_for_model", external_dag_id="create_model")

    ets >> [
        evaluation_data,
        model,
    ]

    evaluation_results = evaluate_model(model, evaluation_data)
    notify_msteams(evaluation_results)
    evaluation_results >> EmailOperator(
        task_id="send_email_sad",
        to="s24477@pjwstk.edu.pl",
        subject="Model evaluation results",
        html_content=f"Model accuracy: {evaluation_results}",
    )


monitor_model()
