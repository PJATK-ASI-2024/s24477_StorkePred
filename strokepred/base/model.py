from pycaret.classification import setup

from strokepred.base.dataset import create_train_dataset, RANDOM_STATE

import pandas as pd


def create_model_strokepred(df_train: pd.DataFrame, df_test: pd.DataFrame):
    s = setup(
        data=df_train,
        test_data=df_test,
        target="stroke",
        session_id=RANDOM_STATE,
        verbose=False,
        preprocess=False,
    )

    strokepred_model = s.create_model("rf", verbose=False)

    return strokepred_model, s

if __name__ == "__main__":
    model, sm = create_model_strokepred(*create_train_dataset())

    print(model)
    (_, path) = sm.save_model(model, "strokepred_model")

    print(f"Save model to {path}")
