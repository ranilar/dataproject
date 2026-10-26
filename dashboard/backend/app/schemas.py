from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CohortKey = Literal["HARMONIZED", "CLINICAL", "WEARABLE"]
Sex = Literal["ALL", "M", "F"]
Mood = Literal["Happy", "Neutral", "Sad", "Stressed"]
AlertType = Literal["warning", "danger", "success"]
Tier = Literal["emerald", "sky", "amber", "rose"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Metrics(StrictModel):
    sleep_hours: float = Field(ge=0, le=24)
    stress_level: float = Field(ge=0, le=10)
    daily_steps: float = Field(ge=0, le=200_000)
    heart_rate: float = Field(ge=20, le=250)
    endurance_level: float = Field(ge=0, le=100)
    bmi: float = Field(ge=5, le=100)
    hydration_level: float = Field(ge=0, le=20)


class ScoreRequest(StrictModel):
    values: Metrics
    cohort: CohortKey = "HARMONIZED"
    sex: Sex = "ALL"
    mood: Mood = "Neutral"
    age: int = Field(38, ge=0, le=120)
    active_minutes: float = Field(75, ge=0, le=1440)
    auto_endurance: bool = True


class Verdict(BaseModel):
    tier: Tier
    title: str
    description: str


class Percentile(BaseModel):
    z: float
    pct: float
    mean: float


class Alert(BaseModel):
    type: AlertType
    title: str
    description: str
    deduction: float


class Roi(BaseModel):
    id: str
    label: str
    gain: float


class HydrationTarget(BaseModel):
    target: float
    low: float
    high: float
    label: str


class ScoreResponse(BaseModel):
    score: float
    total_deduction: float
    verdict: Verdict
    values: Metrics  # effective inputs, incl. auto-computed endurance
    sub_scores: dict[str, float]
    percentiles: dict[str, Percentile]
    alerts: list[Alert]
    roi: Optional[Roi]
    hydration_target: HydrationTarget


class ParamSpec(BaseModel):
    id: str
    name: str
    unit: str
    min: float
    max: float
    step: float
    default: float
    info: str


class CohortInfo(BaseModel):
    name: str
    count: int
    means: dict[str, float]


class ConfigResponse(BaseModel):
    params: list[ParamSpec]
    cohorts: dict[str, CohortInfo]
    profiles: list[str]


class Profile(BaseModel):
    values: dict[str, float]  # partial: sample logs omit endurance
    active_minutes: float
    mood: Mood


class ParseLogRequest(StrictModel):
    raw: str = Field(max_length=10_000)


class ParsedLog(BaseModel):
    values: dict[str, float]
    active_minutes: Optional[float]
    mood: Optional[Mood]
