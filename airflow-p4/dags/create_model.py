from airflow.decorators import dag, task
from datetime import datetime
from airflow import Dataset

from pycaret.classification import setup

from pathlib import Path
import pandas as pd


@dag(
    schedule=[Dataset("/opt/airflow/all.csv")],
    dag_display_name="Create Model",
    dag_id="create_model",
    start_date=datetime(2024, 11, 22),
)
def create_model_dag():
    @task()
    def create_model():
        df = pd.read_csv("/opt/airflow/all.csv")
        df_train = df.sample(frac=0.7, random_state=123)
        df_test = df.drop(df_train.index)
        print(df_train)
        print(df_test)

        return {
            "df_train": df_train,
            "df_test": df_test,
        }

    @task()
    def compare_models(inputs):
        df_train = inputs["df_train"]
        df_test = inputs["df_test"]

        s = setup(
            data=df_train,
            test_data=df_test,
            target="stroke",
            session_id=312678,
            verbose=False,
            preprocess=False,
        )

        best_model = s.compare_models(
            include=[
                # "catboost",
                "lr",
                "knn",
                "nb",
                "dt",
                "svm",
                "ridge",
                "rf",
                "qda",
                "ada",
                "gbc",
                "lda",
                "et",
            ],
            verbose=False,
            # n_select=3,
        )

        model_comparison = s.pull()

        print(model_comparison)

        Path("/opt/airflow/models").mkdir(exist_ok=True)
        Path("/opt/airflow/reports").mkdir(exist_ok=True)

        with open("/opt/airflow/reports/model_comparison.txt", "w", encoding="utf8") as f:
            f.write(str(model_comparison))

        s.save_model(best_model, "/opt/airflow/models/best_model")

    data = create_model()
    compare_models(data)
    # data_task
    # create_model()


create_model_dag()
