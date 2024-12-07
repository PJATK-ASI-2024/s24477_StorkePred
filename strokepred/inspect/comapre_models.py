from pycaret.classification import setup

from strokrepred.base.dataset import create_train_dataset, RANDOM_STATE

(df_train, df_test) = create_train_dataset()

s = setup(
    data=df_train,
    test_data=df_test,
    target="stroke",
    session_id=RANDOM_STATE,
    verbose=False,
    preprocess=False,
)

best_models = s.compare_models(
    # Following models are not Turbo comp
    # exclude=["rbfsvm", "gpc", "mlp", "et", "lda", "gbc"]
    # Choosing lightweight models
    include=[
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
    n_select=3,
)

model_comparison = s.pull()

if __name__ == "__main__":
    print(model_comparison)
