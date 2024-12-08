import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pycaret.classification import load_model, setup

from strokepred.api.models import StrokepredInputs, StrokepredPredictions
from strokepred.base.dataset import RANDOM_STATE, create_dataset, create_train_dataset

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


@app.get("/", summary="Redirects to the documentation")
def read_root():
    """
    Redirects to the documentation.

    Returns:
    --------
    RedirectResponse
        Redirects to the documentation
    """
    return RedirectResponse(url="/docs")


@app.get("/sample", summary="Returns a sample of the dataset")
def read_sample(count: int = 10) -> StrokepredInputs:
    """
    Reads a sample of the dataset, useful for testing the API.

    Parameters:
    -----------
    count: int
        Number of samples to return, max is 50 values.

    Returns:
    --------
    StrokepredInputs
        Sample of the dataset
    """
    if count > 50:
        raise HTTPException(400, detail="Count must be less than 50.")

    sample = df_source.sample(count)
    return StrokepredInputs.model_validate({"data": sample.to_dict("records")})


@app.post("/predict", summary="Predicts the stroke probability")
def predict(strokepred: StrokepredInputs) -> StrokepredPredictions:
    """
    Returns the predictions of the model for the given input data.

    Parameters:
    -----------
    strokepred: StrokepredInputs
        Input data to predict, can be aquired from the /sample endpoint.
        Maximum of 50 samples.

    Returns:
    --------
    StrokepredPredictions
        Predictions of the model
    """
    if len(strokepred.data) > 50:
        raise HTTPException(400, detail="Count must be less than 50.")

    df_inputs = pd.DataFrame(strokepred.model_dump()["data"])

    # moneky patch the df types for get_dummies (categories are must have)
    # this is code is a required for the model to encode all columns correctly
    for col in df_inputs.columns:
        if df_source[col].dtype == "category":
            df_inputs[col] = pd.Categorical(
                df_inputs[col], categories=df_source[col].cat.categories
            )

    df_encoded = pd.get_dummies(df_inputs)

    predictions = s.predict_model(model, data=df_encoded)
    predictions = predictions[["prediction_label", "prediction_score"]]
    predictions = predictions.rename(
        {"prediction_label": "result", "prediction_score": "score"}, axis=1
    )

    return StrokepredPredictions.model_validate(
        {"data": predictions.to_dict("records")}
    )
