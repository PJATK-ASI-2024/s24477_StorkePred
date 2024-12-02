from airflow.decorators import dag, task
from datetime import datetime
from airflow import Dataset

from pycaret.classification import setup

from pathlib import Path
import pandas as pd

from notify import notify_failure, notify_success

@dag(
    schedule=[Dataset("/opt/airflow/all.csv")],
    dag_display_name="Create Model",
    dag_id="create_model",
    start_date=datetime(2024, 11, 22),
    on_failure_callback=notify_failure,
    on_success_callback=notify_success,
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

    @task(multiple_outputs=True)
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

        Path("/opt/airflow/models").mkdir(exist_ok=True)
        s.save_model(best_model, "/opt/airflow/models/best_model")

        return {
            "best_model": best_model,
            "model_comparison": s.pull(),
            # "setup_output": s,
        }

    @task()
    def monitor_model(model_comparison: pd.DataFrame):
        # check model accuracy, check first row
        best_model = model_comparison.head(1).to_dict(orient="records")[0]
        if best_model["Accuracy"] > 0.8:
            print("Model accuracy is greater than 0.8")
        else:
            print("Model accuracy is less than 0.8")
            raise ValueError("Model accuracy is less than 0.8")
        # print(model_comparison.head(1)['Accuracy'] > 0.8)


        # print(model_comparison)

    @task()
    def save_model(best_model, model_comparison, setup_output):
        Path("/opt/airflow/reports").mkdir(exist_ok=True)

        with open("/opt/airflow/reports/model_comparison.txt", "w", encoding="utf8") as f:
            f.write(str(model_comparison))



    data = create_model()
    compout = compare_models(data)
    save_model(compout["best_model"], compout["model_comparison"], compout["setup_output"])
    monitor_model(compout["model_comparison"])
    # data_task
    # create_model()


create_model_dag()
