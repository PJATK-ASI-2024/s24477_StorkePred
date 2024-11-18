from airflow.decorators import dag, task

from datetime import datetime
import pandas as pd

import gspread
import os


@dag(schedule_interval="@daily", start_date=datetime.now(), catchup=False)
def download_and_preprocess():
    @task()
    def download_from_google_seets():
        gc = gspread.service_account()
        sh = gc.open_by_url(os.getenv("GOOGLE_SHEETS_URL"))
        worksheet = sh.worksheet("train")
        data = worksheet.get_all_values()
        return pd.DataFrame(data[1:], columns=data[0])

    @task()
    def remove_outliers(df: pd.DataFrame):
        # Remove "Other"
        df = df[df["gender"] != "Other"]

        # Remove bmi outliers
        df = df[df["bmi"] < 65]

        return df

    @task()
    def fill_missing_values(df: pd.DataFrame):
        return df["bmi"].fillna(df["bmi"].median())

    @task()
    def remap_values(df: pd.DataFrame):
        df = df.drop(columns=["id"])

        # Remap ever married into boolean values
        df["ever_married"] = df["ever_married"] == "Yes"
        # Remap hypertension into boolean values
        df["hypertension"] = df["hypertension"] == 1
        # Remap heart_disease into boolean values
        df["heart_disease"] = df["heart_disease"] == 1
        # Remap stroke into boolean values
        df["stroke"] = df["stroke"] == 1

        return df

    @task()
    def encode_normalize(df: pd.DataFrame):
        return pd.get_dummies(df)

    @task()
    def upload_to_google_sheets(df: pd.DataFrame, scope: str):
        gc = gspread.service_account()
        sh = gc.open_by_url(os.getenv("GOOGLE_SHEETS_URL"))
        worksheet = sh.worksheet(scope)
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        print(df)

    df = download_from_google_seets()
    df = remove_outliers(df)
    df = fill_missing_values(df)
    df = remap_values(df)
    df = encode_normalize(df)
    upload_to_google_sheets(df, "preprocessed")


download_and_preprocess()
