FROM apache/airflow:2.10.3-python3.11

USER root

RUN apt update && apt install -y libgomp1 build-essential

RUN mkdir -p /home/airflow/

RUN chown -R airflow /home/airflow/

RUN chmod 777 -R /home/airflow

USER airflow

WORKDIR /opt/airflow

RUN pip install pipx

RUN pipx install poetry

RUN pipx inject poetry poetry-plugin-export

COPY pyproject.toml poetry.lock /opt/airflow/

RUN poetry export --only main,airflow,api --without-hashes --format=requirements.txt > requirements.txt

# COPY airflow2/requirements.txt /opt/airflow/requirements.txt

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

ENV STROKEPRED_HOME="/opt/airflow/strokepred"

COPY strokepred/__init__.py ${STROKEPRED_HOME}/__init__.py

COPY strokepred/base/ ${STROKEPRED_HOME}/base/

ENV PYTHONPATH="${STROKEPRED_HOME}:${PYTHONPATH}"

# RUN pip install apache-airflow-providers-docker apache-airflow-providers-microsoft-azure pymsteams gspread pandas kagglehub pycaret kaleido matplotlib imbalanced-learn