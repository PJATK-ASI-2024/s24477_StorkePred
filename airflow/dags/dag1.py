from datetime import datetime
from pathlib import Path

import kagglehub
import pandas as pd
from airflow.decorators import dag, task

import gspread
import os

RANDOM_STATE = 54322543


@dag(schedule_interval="@daily", start_date=datetime.now(), catchup=False)
def download_and_split():

    @task()
    def download_from_kaggle():
        dataset_path = kagglehub.dataset_download(
            "fedesoriano/stroke-prediction-dataset"
        )

        dataset_path = Path(dataset_path) / "healthcare-dataset-stroke-data.csv"

        df = pd.read_csv(dataset_path)

        return df

    # split 70/30, i don't need special lib for this...
    @task(multiple_outputs=True)
    def split_df(df):
        df_train = df.sample(frac=0.7, random_state=RANDOM_STATE)
        df_test = df.drop(df_train.index)

        return {
            "train": df_train,
            "test": df_test,
        }

    @task()
    def upload_to_google_sheets(df: pd.DataFrame, scope: str):
        gc = gspread.service_account()
        sh = gc.open_by_url(os.getenv("GOOGLE_SHEETS_URL"))
        worksheet = sh.worksheet(scope)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    df = download_from_kaggle()
    dfs = split_df(df)
    upload_to_google_sheets(dfs["train"], "train")
    upload_to_google_sheets(dfs["test"], "test")


download_and_split()
