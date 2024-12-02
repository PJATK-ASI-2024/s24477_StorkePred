from datetime import datetime
from pathlib import Path

import airflow
import os
import kagglehub
import pandas as pd
from airflow.decorators import dag, task
from imblearn.over_sampling import SMOTE
from airflow.operators.empty import EmptyOperator

from airflow import Dataset

RANDOM_STATE = 54322543


@dag(
    schedule_interval="@once",
    start_date=datetime(2024, 11, 1),
    catchup=True,
    dag_display_name="Create Dataset",
    dag_id="create_data",
)
def create_model_dag():
    def sanitize_dataset(df: pd.DataFrame):
        """
        Removes outliers and fills missing values in the dataset.
        Also perform remaps on int values to boolean values (if possible).
        Based on results from the EDA notebook.
        """
        # Drop id
        df = df.drop(columns=["id"])

        # Fill missing bmi values
        df["bmi"] = df["bmi"].fillna(df["bmi"].median())

        # Remove "Other"
        df = df[df["gender"] != "Other"]
        # df["gender"] = df["gender"].isin(["Male", "Female"])

        # Remove bmi outliers
        df = df[df["bmi"] < 65]

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
    def download_file():
        """
        Downloads the stroke prediction dataset.
        """
        dataset_path = kagglehub.dataset_download(
            "fedesoriano/stroke-prediction-dataset"
        )

        dataset_path = Path(dataset_path) / "healthcare-dataset-stroke-data.csv"

        return dataset_path

    @task()
    def create_dataset(path: str, raw=False):
        """
        Returns the stroke prediction dataset.
        """
        dataset_path = path

        df = pd.read_csv(dataset_path)

        if raw:
            return df

        # Drop id
        df = sanitize_dataset(df)

        return df

    @task(multiple_outputs=True)
    def split_encoded_dataset(df_raw: pd.DataFrame):
        """
        Splits the dataset into a training and tuning set.
        Performs one-hot encoding on the dataset.
        """
        df = pd.get_dummies(df_raw)

        train_df = df.sample(frac=0.7, random_state=RANDOM_STATE)
        tune_df = df.drop(train_df.index)

        return {
            "train": train_df,
            "tune": tune_df,
        }

    @task()
    def balanced_dataset(df_encoded: pd.DataFrame):
        # balance the dataset
        smote = SMOTE(random_state=RANDOM_STATE)
        X = df_encoded.drop("stroke", axis=1)
        y = df_encoded["stroke"]
        X_balanced, y_balanced = smote.fit_resample(X, y)
        df_balanced = pd.concat(
            [
                pd.DataFrame(X_balanced, columns=X.columns),
                pd.Series(y_balanced, name="stroke"),
            ],
            axis=1,
        )

        return df_balanced

    @task()
    def create_train_dataset(df_balanced: pd.DataFrame):
        df_balanced_train = df_balanced.sample(frac=0.7, random_state=RANDOM_STATE)
        df_balanced_test = df_balanced.drop(df_balanced_train.index)

        return {
            "train": df_balanced_train,
            "test": df_balanced_test,
        }

    @task(outlets=[Dataset("/opt/airflow/train.csv"), Dataset("/opt/airflow/test.csv"), Dataset("/opt/airflow/all.csv")])
    def save_train_dataset(df_train_datasets: dict, df_balanced: pd.DataFrame):
        df_balanced.to_csv("/opt/airflow/all.csv", index=False)
        df_train_datasets["train"].to_csv("/opt/airflow/train.csv", index=False)
        df_train_datasets["test"].to_csv("/opt/airflow/test.csv", index=False)

    path = download_file()
    df_raw = create_dataset(path)
    df_encoded = split_encoded_dataset(df_raw)
    df_balanced = balanced_dataset(df_encoded["train"])
    df_train_datasets = create_train_dataset(df_balanced)
    save_train_dataset(df_train_datasets, df_balanced)


    # return df_train_datasets
    # print(df_train_test)


create_model_dag()
