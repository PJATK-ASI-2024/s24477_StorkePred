FROM python:3.11.10-slim AS base

RUN apt update && apt install -y libgomp1

ENV USER=app-strokepred

# Make a user to run the app
RUN useradd -m ${USER}

USER ${USER}

ENV PATH="/home/${USER}/.local/bin:${PATH}"

RUN pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

ENV PYTHONPATH="/app:${PYTHONPATH}"

RUN poetry install --only main

COPY strokepred/model.py strokepred/dataset.py /app/strokepred/

RUN poetry run python3 strokepred/model.py

FROM base AS jupyter

RUN poetry install --with notebook

COPY eda.ipynb strokrepred.ipynb /app/

CMD ["poetry", "run", "jupyter", "notebook", "--ip=0.0.0.0"]

FROM base AS api

RUN poetry install --only main,api

COPY strokepred/api.py /app/strokepred/

CMD ["poetry", "run", "fastapi", "run", "strokepred/api.py", "--host", "0.0.0.0", "--port", "5000"]