FROM apache/airflow:2.10.2-python3.11

USER root

RUN apt update

RUN apt install libgomp1

USER airflow

RUN pip install --no-cache-dir --upgrade pip

RUN pip install pandas kagglehub pycaret "kaleido==0.2.1" "matplotlib<3.8.0" "imbalanced-learn==0.12.4" apache-airflow pymsteams