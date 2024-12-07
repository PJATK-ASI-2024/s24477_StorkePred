from pycaret.classification import setup

from strokepred.base.dataset import create_train_dataset, RANDOM_STATE

(df_train, df_test) = create_train_dataset()

s = setup(
    data=df_train,
    test_data=df_test,
    target="stroke",
    session_id=RANDOM_STATE,
    verbose=False,
    preprocess=False,
)

strokepred_model = s.create_model("rf", verbose=False)

if __name__ == "__main__":
    print(strokepred_model)
    (_, path) = s.save_model(strokepred_model, "strokepred_model")
    print(f"Save model to {path}")
