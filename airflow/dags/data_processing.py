import os
from datetime import datetime
from pathlib import Path

import gspread
import kagglehub
import pandas as pd
from airflow.decorators import dag, task

from strokepred.base import RANDOM_STATE, sanitize_dataset


@dag(
    schedule_interval="@once",
    start_date=datetime.now(),
    catchup=False,
    dag_display_name="Data Processing",
)
def data_processing():
    @task()
    def download_dataset():
        dataset_path = kagglehub.dataset_download(
            "fedesoriano/stroke-prediction-dataset"
        )

        dataset_path = Path(dataset_path) / "healthcare-dataset-stroke-data.csv"
        return dataset_path

    @task()
    def convert_to_dataframe(csv_path):
        dataset_df = pd.read_csv(csv_path)
        return dataset_df

    @task()
    def sanitize_data(dataframe):
        dataframe = sanitize_dataset(dataframe)
        return dataframe

    @task()
    def split_data(df):
        df_tune = df.sample(frac=0.3, random_state=RANDOM_STATE)
        df_train_phase = df.drop(df_tune.index)
        df_train = df_train_phase.sample(frac=0.7, random_state=RANDOM_STATE)
        df_test = df_train_phase.drop(df_train.index)
        return {
            "tune": df_tune,
            "train": df_train,
            "test": df_test,
        }

    @task()
    def publish_to_google_sheets(x):
        gc = gspread.service_account()

        spreadsheet = gc.open(os.getenv("STROKEPRED_SHEET_URL"))

        # remove existing worksheets
        for sheet in spreadsheet.worksheets():
            spreadsheet.del_worksheet(sheet)

        # create new worksheets
        for name, df in x.items():
            wks = spreadsheet.add_worksheet(title=name, rows=len(df) + 1, cols=len(df.columns))
            wks.update([df.columns.values.tolist()] + df.values.tolist())

        return

    dataset_raw = download_dataset()
    dataset_df = convert_to_dataframe(dataset_raw)
    dataset_clean = sanitize_data(dataset_df)
    dataset_sets = split_data(dataset_clean)
    publish_to_google_sheets(dataset_sets)


data_processing()
