import os
from datetime import datetime

import gspread
import pandas as pd
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.sensors.external_task import ExternalTaskSensor

from strokepred.base import create_model_strokepred


@dag(
    schedule_interval="@once",
    start_date=datetime.now(),
    catchup=False,
    dag_display_name="Model training",
)
def create_model():
    @task()
    def download_datasets_from_google_sheets():
        # download train + test
        gc = gspread.service_account()
        spreadsheet = gc.open(os.getenv("STROKEPRED_SHEET_URL"))
        wks_train = spreadsheet.worksheet("train")
        wks_test = spreadsheet.worksheet("test")

        train_df = pd.DataFrame(wks_train.get_all_records())
        test_df = pd.DataFrame(wks_test.get_all_records())

        return {
            "train": train_df,
            "test": test_df,
        }

    @task()
    def begin_learning(dfs):
        model, s = create_model_strokepred(dfs['train'], dfs['test'])
        return {
            "model": model,
            "setup": s,
        }

    @task()
    def save_model(model_setup):
        model_path = model_setup['model'].save("strokepred_model")
        Variable.set("STROKEPRED_MODEL_PATH", model_path)
        return model_path

    ets = ExternalTaskSensor(task_id="sensor_for_data_processing", external_dag_id='data_processing')
    datasets = download_datasets_from_google_sheets()

    ets >> datasets

    model = begin_learning(datasets)
    save_model(model)

create_model()
