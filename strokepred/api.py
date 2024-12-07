import pandas as pd
from fastapi import FastAPI
from pycaret.classification import load_model, setup

from strokepred.api_models import StrokepredInputs, StrokepredPredictions
from strokepred.dataset import RANDOM_STATE, create_dataset, create_train_dataset

app = FastAPI()

(df_train, df_test) = create_train_dataset()
df_source = create_dataset().drop("stroke", axis=1)

model = load_model("strokepred_model")

s = setup(
    data=df_train,
    test_data=df_test,
    target="stroke",
    session_id=RANDOM_STATE,
    verbose=False,
    preprocess=False,
)


@app.get("/rand_sample")
def read_sample(count: int = 10) -> StrokepredInputs:
    sample = df_source.sample(count)
    return StrokepredInputs.model_validate({"data": sample.to_dict("records")})


@app.post("/predict")
def encode_data(strokepred: StrokepredInputs) -> StrokepredPredictions:
    df_m = pd.DataFrame(strokepred.model_dump()["data"])

    # moneky patch the df types for get_dummies
    for col in df_m.columns:
        if df_source[col].dtype == "category":
            df_m[col] = pd.Categorical(
                df_m[col], categories=df_source[col].cat.categories
            )

    df_encoded = pd.get_dummies(df_m)

    predictions = s.predict_model(model, data=df_encoded)
    predictions = predictions[["prediction_label", "prediction_score"]]
    predictions = predictions.rename(
        {"prediction_label": "result", "prediction_score": "score"}, axis=1
    )

    return StrokepredPredictions.model_validate(
        {"data": predictions.to_dict("records")}
    )
