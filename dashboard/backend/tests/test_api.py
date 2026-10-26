import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.reference import PARAM_SPECS

client = TestClient(app)

DEFAULTS = {p["id"]: p["default"] for p in PARAM_SPECS}


def score(**overrides):
    body = {"values": {**DEFAULTS, **overrides.pop("values", {})}, **overrides}
    return client.post("/api/score", json=body)


def test_config_hides_weights_and_sds():
    res = client.get("/api/config")
    assert res.status_code == 200
    body = res.json()
    assert [p["id"] for p in body["params"]] == list(DEFAULTS)
    assert all("weight" not in p for p in body["params"])
    assert set(body["cohorts"]) == {"HARMONIZED", "CLINICAL", "WEARABLE"}
    assert "std" not in str(body["cohorts"])


def test_default_inputs_score_high():
    res = score()
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["score"] <= 100
    assert body["verdict"]["tier"] == "emerald"
    assert body["alerts"] == []


def test_burnout_profile_triggers_alerts_and_low_score():
    profile = client.get("/api/profiles/burnout").json()
    res = score(values=profile["values"])
    body = res.json()
    titles = {a["title"] for a in body["alerts"]}
    assert "Allostatic Burnout & Sleep Debt" in titles
    assert body["score"] < 45
    assert body["verdict"]["tier"] == "rose"
    assert body["roi"] is not None


@pytest.mark.parametrize("bmi, title", [
    (17.5, "Underweight Clinical Concern"),
    (32.0, "Obesity Class Health Concern"),
])
def test_bmi_concern_alerts(bmi, title):
    alerts = score(values={"bmi": bmi}).json()["alerts"]
    assert [a["title"] for a in alerts if a["type"] == "danger"] == [title]


def test_no_bmi_alert_inside_range():
    assert not any("BMI" in a["description"] for a in score(values={"bmi": 26.0}).json()["alerts"])


def test_defaults_are_dataset_medians():
    params = {p["id"]: p for p in client.get("/api/config").json()["params"]}
    assert params["sleep_hours"]["default"] == 7.0
    assert params["stress_level"]["default"] == 5.0
    assert 80 <= score().json()["score"] <= 90  # a typical person, not a perfect 100


def test_config_has_dataset_ranges():
    ranges = client.get("/api/config").json()["cohorts"]
    assert ranges["CLINICAL"]["ranges"]["bmi"] == [18.5, 24.9]
    assert ranges["WEARABLE"]["ranges"]["endurance_level"] is None  # Dataset 2 has no endurance


def test_hydration_target_depends_on_sex():
    assert score(sex="M").json()["hydration_target"]["target"] == 3.7
    assert score(sex="F").json()["hydration_target"]["target"] == 2.7


@pytest.mark.parametrize("body", [
    {"values": {**DEFAULTS, "bmi": "nan"}},
    {"values": {k: v for k, v in DEFAULTS.items() if k != "bmi"}},
    {"values": DEFAULTS, "mood": "Happy"},  # mood was removed from the API
    {"values": DEFAULTS, "cohort": "OTHER"},
    {"values": DEFAULTS, "unexpected": 1},
])
def test_invalid_score_requests_rejected(body):
    assert client.post("/api/score", json=body).status_code == 422


def test_profile_hydration_by_sex_and_unknown_profile():
    assert client.get("/api/profiles/athlete?sex=M").json()["values"]["hydration_level"] == 4.0
    assert client.get("/api/profiles/athlete?sex=F").json()["values"]["hydration_level"] == 3.2
    assert client.get("/api/profiles/report_optimal").status_code == 404
    assert client.get("/api/profiles/nope").status_code == 404


def test_frontend_served_at_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "app.js" in res.text
