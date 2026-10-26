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
    res = score(mood="Happy")
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["score"] <= 100
    assert body["verdict"]["tier"] == "emerald"
    assert any(a["type"] == "success" for a in body["alerts"])


def test_burnout_profile_triggers_alerts_and_low_score():
    profile = client.get("/api/profiles/burnout").json()
    res = score(values=profile["values"], mood=profile["mood"], active_minutes=profile["active_minutes"])
    body = res.json()
    titles = {a["title"] for a in body["alerts"]}
    assert "Allostatic Burnout & Sleep Debt" in titles
    assert body["score"] < 45
    assert body["verdict"]["tier"] == "rose"
    assert body["roi"] is not None


def test_auto_endurance_overrides_input():
    on = score(values={"endurance_level": 4.0}, auto_endurance=True).json()
    off = score(values={"endurance_level": 4.0}, auto_endurance=False).json()
    assert on["values"]["endurance_level"] != 4.0
    assert off["values"]["endurance_level"] == 4.0


def test_hydration_target_depends_on_sex():
    assert score(sex="M").json()["hydration_target"]["target"] == 3.7
    assert score(sex="F").json()["hydration_target"]["target"] == 2.7


@pytest.mark.parametrize("body", [
    {"values": {**DEFAULTS, "bmi": "nan"}},
    {"values": {k: v for k, v in DEFAULTS.items() if k != "bmi"}},
    {"values": DEFAULTS, "mood": "Angry"},
    {"values": DEFAULTS, "cohort": "OTHER"},
    {"values": DEFAULTS, "unexpected": 1},
])
def test_invalid_score_requests_rejected(body):
    assert client.post("/api/score", json=body).status_code == 422


def test_profile_hydration_by_sex_and_unknown_profile():
    assert client.get("/api/profiles/report_optimal?sex=M").json()["values"]["hydration_level"] == 3.7
    assert client.get("/api/profiles/report_optimal?sex=F").json()["values"]["hydration_level"] == 2.7
    assert client.get("/api/profiles/nope").status_code == 404


def test_parse_log_json_and_csv():
    res = client.post("/api/parse-log", json={"raw": '{"Hours_Slept": 6.8, "Steps_Taken": 9400, "Heart_Rate": 74, "Mood": "Happy"}'})
    assert res.json() == {
        "values": {"sleep_hours": 6.8, "daily_steps": 9400, "heart_rate": 74},
        "active_minutes": None,
        "mood": "Happy",
    }
    res = client.post("/api/parse-log", json={"raw": "7.5, 8000, 65, 4, 23.1"})
    assert res.json()["values"] == {"sleep_hours": 7.5, "daily_steps": 8000, "heart_rate": 65, "stress_level": 4, "bmi": 23.1}


@pytest.mark.parametrize("raw", ["{not json", "[1, 2]", "1, 2", '{"Mood": "Angry"}', '{"Hours_Slept": "abc"}', "{}"])
def test_parse_log_errors(raw):
    res = client.post("/api/parse-log", json={"raw": raw})
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], str)


def test_frontend_served_at_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "app.js" in res.text
