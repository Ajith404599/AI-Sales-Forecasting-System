from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import joblib
import numpy as np
import pandas as pd

from app.api import models as models_api
from app.main import app
from app.models.model_run import ModelRun
from app.models.product import Product
from app.models.sale import Sale
from app.models.user import User
from app.services import forecasting_service
from app.services.forecasting_service import (
    FEATURE_COLUMNS,
    build_training_frame,
    calculate_regression_metrics,
    forecast_and_record,
    train_and_activate_model,
)


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _add_daily_sales(db_session, days=140):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    products = db_session.query(Product).filter(Product.product_id.in_([1, 2])).all()
    start_date = (datetime.now() - timedelta(days=days + 10)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    for day_offset in range(days):
        for product in products:
            quantity = 2 + (day_offset % 7) + product.product_id
            unit_price = Decimal("10.00") + Decimal(product.product_id) + Decimal(day_offset % 3)
            db_session.add(Sale(
                product_id=product.product_id,
                user_id=user.user_id,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=Decimal("0.00"),
                total_amount=unit_price * quantity,
                sale_date=start_date + timedelta(days=day_offset),
            ))
    db_session.commit()


def test_feature_engineering_uses_only_prior_observations():
    start_date = pd.Timestamp("2025-01-01")
    sales = pd.DataFrame([
        {
            "product_id": 1,
            "category": "Test",
            "quantity": day_offset + 1,
            "unit_price": 20 + day_offset,
            "sale_date": start_date + pd.Timedelta(days=day_offset),
        }
        for day_offset in range(40)
    ])

    frame = build_training_frame(sales)
    target_day = start_date + pd.Timedelta(days=30)
    row = frame.loc[frame["sale_date"] == target_day].iloc[0]
    assert row["quantity"] == 31
    assert row["lag_1"] == 30
    assert row["lag_7"] == 24
    assert row["rolling_mean_7"] == 27
    assert row["rolling_mean_28"] == 16.5
    assert row["price"] == 49


def test_metric_calculation_uses_real_holdout_values():
    metrics = calculate_regression_metrics([1, 2, 3], [1, 2, 4])
    assert metrics["mae"] == 1 / 3
    assert np.isclose(metrics["rmse"], np.sqrt(1 / 3))
    assert metrics["r2"] == 0.5


def test_training_compares_persists_and_failure_preserves_active_model(db_session, tmp_path, monkeypatch):
    _add_daily_sales(db_session)
    result = train_and_activate_model(db_session, artifact_dir=tmp_path)

    assert result["training_status"] == "succeeded"
    assert result["training_records"] >= 60
    assert result["evaluation_records"] >= 2
    assert {candidate["model_name"] for candidate in result["candidates"]} == {
        "Linear Regression",
        "Random Forest Regressor",
        "Gradient Boosting Regressor",
    }
    assert all(np.isfinite(candidate["mae"]) for candidate in result["candidates"])
    assert all(np.isfinite(candidate["rmse"]) for candidate in result["candidates"])
    assert all(np.isfinite(candidate["r2"]) for candidate in result["candidates"])

    version_runs = db_session.query(ModelRun).filter(ModelRun.model_version == result["model_version"]).all()
    assert len(version_runs) == 3
    active_run = next(model_run for model_run in version_runs if model_run.is_active)
    assert active_run.model_name == result["selected_model"]
    assert active_run.training_status == "succeeded"
    artifact_path = tmp_path / f"sales_forecast_{result['model_version']}.pkl"
    assert artifact_path.is_file()
    saved_bundle = joblib.load(artifact_path)
    assert saved_bundle["model_version"] == result["model_version"]
    assert saved_bundle["feature_columns"] == FEATURE_COLUMNS
    assert saved_bundle["pipeline"].predict(
        build_training_frame(pd.DataFrame([
            {
                "product_id": 1,
                "category": "Electronics",
                "quantity": day_offset + 1,
                "unit_price": 20,
                "sale_date": datetime(2025, 1, 1) + timedelta(days=day_offset),
            }
            for day_offset in range(40)
        ]))[FEATURE_COLUMNS].head(1)
    ).shape == (1,)

    previous_active_id = active_run.model_run_id
    previous_artifact = active_run.artifact_path
    monkeypatch.setattr(forecasting_service, "load_historical_sales", lambda _db: pd.DataFrame())
    failed = train_and_activate_model(db_session, artifact_dir=tmp_path)
    db_session.expire_all()

    assert failed["training_status"] == "failed"
    assert db_session.query(ModelRun).filter(ModelRun.is_active.is_(True)).one().model_run_id == previous_active_id
    assert (tmp_path / previous_artifact.split("/")[-1]).is_file() or (tmp_path / previous_artifact.split("\\")[-1]).is_file()
    failed_run = db_session.query(ModelRun).filter(ModelRun.model_version == failed["model_version"]).one()
    assert failed_run.training_status == "failed"
    assert failed_run.error_message


def test_forecast_api_persists_prediction_and_actual_value(client, db_session, staff_token, manager_token, tmp_path):
    _add_daily_sales(db_session)
    result = train_and_activate_model(db_session, artifact_dir=tmp_path)
    assert result["training_status"] == "succeeded"

    response = client.post(
        "/forecast/predict",
        json={"product_id": 1, "horizon_days": 2},
        headers=_auth(staff_token),
    )
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["prediction_id"] > 0
    assert prediction["product_id"] == 1
    assert prediction["horizon_days"] == 2
    assert Decimal(prediction["predicted_quantity"]) >= 0
    assert prediction["model_version"] == result["model_version"]

    history = client.get("/predictions?product_id=1", headers=_auth(staff_token))
    assert history.status_code == 200
    assert any(row["prediction_id"] == prediction["prediction_id"] for row in history.json())
    searched = client.get("/predictions?search=Electronics", headers=_auth(staff_token))
    assert searched.status_code == 200
    assert any(row["prediction_id"] == prediction["prediction_id"] for row in searched.json())
    forbidden_history = client.get("/predictions?user_id=1", headers=_auth(staff_token))
    assert forbidden_history.status_code == 403

    staff_actual = client.patch(
        f"/predictions/{prediction['prediction_id']}/actual",
        json={"actual_quantity": 5},
        headers=_auth(staff_token),
    )
    assert staff_actual.status_code == 403
    manager_actual = client.patch(
        f"/predictions/{prediction['prediction_id']}/actual",
        json={"actual_quantity": 5},
        headers=_auth(manager_token),
    )
    assert manager_actual.status_code == 200
    assert Decimal(manager_actual.json()["actual_quantity"]) == Decimal("5")


def test_manual_retraining_is_admin_only_and_route_registration(client, staff_token, admin_token, monkeypatch):
    called = []

    def fake_trainer(db):
        called.append(db)
        return {
            "training_status": "succeeded",
            "model_version": "test-version",
            "selected_model": "Linear Regression",
            "training_records": 100,
            "evaluation_records": 20,
            "trained_at": datetime.now(timezone.utc),
            "candidates": [],
            "error_message": None,
        }

    monkeypatch.setattr(models_api, "train_and_activate_model", fake_trainer)
    assert client.post("/forecast/predict", json={"product_id": 1, "horizon_days": 1}).status_code == 401
    assert client.get("/predictions").status_code == 401
    assert client.get("/models/runs").status_code == 401
    denied = client.post("/models/retrain", headers=_auth(staff_token))
    assert denied.status_code == 403
    assert called == []

    allowed = client.post("/models/retrain", headers=_auth(admin_token))
    assert allowed.status_code == 200
    assert allowed.json()["training_status"] == "succeeded"
    assert len(called) == 1

    paths = app.openapi()["paths"]
    assert "post" in paths["/forecast/predict"]
    assert "get" in paths["/predictions"]
    assert "post" in paths["/models/retrain"]
    assert "get" in paths["/models/active"]