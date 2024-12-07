import typing as ty

from pydantic import BaseModel


class StrokepredInput(BaseModel):
    age: int
    gender: ty.Literal["Male", "Female"]
    hypertension: bool
    heart_disease: bool
    ever_married: bool
    work_type: ty.Literal[
        "Private", "Self-employed", "Govt_job", "children", "Never_worked"
    ]
    residence_type: ty.Literal["Urban", "Rural"]
    avg_glucose_level: float
    bmi: float
    smoking_status: ty.Literal["never smoked", "formerly smoked", "smokes", "Unknown"]


class StrokepredInputs(BaseModel):
    data: ty.List[StrokepredInput]


class StrokepredPrediction(BaseModel):
    result: int
    score: float


class StrokepredPredictions(BaseModel):
    data: ty.List[StrokepredPrediction]
