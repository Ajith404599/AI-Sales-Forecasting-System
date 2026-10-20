from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd

from sqlalchemy import func
from sqlalchemy.orm import Session

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.core.config import settings
from app.models.model_run import ModelRun
from app.models.prediction import PredictionHistory
from app.models.product import Product
from app.models.sale import Sale


# ============================================================
# FORECASTING CONFIGURATION
# ============================================================

PREDICTION_TARGET = "daily_quantity"

CATEGORICAL_FEATURES = [
    "product_id",
    "category",
]

NUMERIC_FEATURES = [
    "price",
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "rolling_mean_28",
    "day_of_week",
    "month",
    "quarter",
    "year",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES


class ForecastingError(ValueError):
    """Raised when forecasting cannot be completed."""


# ============================================================
# LOAD SALES DATA FROM MYSQL
# ============================================================

def load_historical_sales(db: Session) -> pd.DataFrame:

    rows = (
        db.query(
            Sale.product_id.label("product_id"),
            Product.category.label("category"),
            Sale.quantity.label("quantity"),
            Sale.unit_price.label("unit_price"),
            Sale.sale_date.label("sale_date"),
        )
        .join(
            Product,
            Product.product_id == Sale.product_id,
        )
        .filter(
            Sale.sale_date.is_not(None),
            Sale.quantity > 0,
        )
        .all()
    )

    records = []

    for row in rows:
        records.append(
            {
                "product_id": row.product_id,
                "category": row.category,
                "quantity": row.quantity,
                "unit_price": row.unit_price,
                "sale_date": row.sale_date,
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "product_id",
            "category",
            "quantity",
            "unit_price",
            "sale_date",
        ],
    )


# ============================================================
# CLEAN HISTORICAL SALES
# ============================================================

def clean_sales_history(
    sales: pd.DataFrame,
) -> pd.DataFrame:

    required = {
        "product_id",
        "category",
        "quantity",
        "unit_price",
        "sale_date",
    }

    missing = required.difference(sales.columns)

    if missing:
        raise ForecastingError(
            "Sales data is missing required fields: "
            + ", ".join(sorted(missing))
        )

    clean = sales[
        [
            "product_id",
            "category",
            "quantity",
            "unit_price",
            "sale_date",
        ]
    ].copy()

    clean["sale_date"] = (
        pd.to_datetime(
            clean["sale_date"],
            errors="coerce",
            utc=True,
        )
        .dt.tz_convert(None)
        .dt.normalize()
    )

    clean["product_id"] = pd.to_numeric(
        clean["product_id"],
        errors="coerce",
    )

    clean["quantity"] = pd.to_numeric(
        clean["quantity"],
        errors="coerce",
    )

    clean["unit_price"] = pd.to_numeric(
        clean["unit_price"],
        errors="coerce",
    )

    clean = clean.dropna(
        subset=[
            "product_id",
            "quantity",
            "sale_date",
        ]
    )

    clean = clean[
        (clean["product_id"] > 0)
        & (clean["quantity"] > 0)
        & (
            clean["unit_price"].isna()
            | (clean["unit_price"] >= 0)
        )
    ]

    clean["product_id"] = clean["product_id"].astype(int)

    clean["category"] = (
        clean["category"]
        .fillna("Unknown")
        .astype(str)
    )

    if clean.empty:
        raise ForecastingError(
            "No valid historical sales records are available."
        )

    return (
        clean.sort_values(
            ["sale_date", "product_id"]
        )
        .reset_index(drop=True)
    )


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_training_frame(
    sales: pd.DataFrame,
) -> pd.DataFrame:

    clean = clean_sales_history(sales)

    clean["price_amount"] = (
        clean["unit_price"] * clean["quantity"]
    )

    daily_sales = (
        clean.groupby(
            [
                "product_id",
                "category",
                "sale_date",
            ],
            as_index=False,
        )
        .agg(
            quantity=("quantity", "sum"),
            price_amount=("price_amount", "sum"),
        )
    )

    daily_sales["observed_price"] = (
        daily_sales["price_amount"]
        / daily_sales["quantity"]
    )

    daily_sales = daily_sales.drop(
        columns="price_amount"
    )

    calendar = pd.DataFrame(
        {
            "sale_date": pd.date_range(
                clean["sale_date"].min(),
                clean["sale_date"].max(),
                freq="D",
            )
        }
    )

    products = (
        daily_sales[
            ["product_id", "category"]
        ]
        .drop_duplicates()
        .copy()
    )

    products["_join_key"] = 1
    calendar["_join_key"] = 1

    frame = (
        products.merge(
            calendar,
            on="_join_key",
        )
        .drop(columns="_join_key")
    )

    frame = frame.merge(
        daily_sales,
        on=[
            "product_id",
            "category",
            "sale_date",
        ],
        how="left",
    )

    frame["quantity"] = (
        pd.to_numeric(
            frame["quantity"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    frame = (
        frame.sort_values(
            ["product_id", "sale_date"]
        )
        .reset_index(drop=True)
    )

    grouped = frame.groupby(
        "product_id",
        sort=False,
    )

    frame["price"] = grouped[
        "observed_price"
    ].transform(
        lambda prices: prices.shift(1).ffill()
    )

    frame["lag_1"] = grouped[
        "quantity"
    ].shift(1)

    frame["lag_7"] = grouped[
        "quantity"
    ].shift(7)

    frame["rolling_mean_7"] = grouped[
        "quantity"
    ].transform(
        lambda quantities: (
            quantities.shift(1)
            .rolling(
                window=7,
                min_periods=7,
            )
            .mean()
        )
    )

    frame["rolling_mean_28"] = grouped[
        "quantity"
    ].transform(
        lambda quantities: (
            quantities.shift(1)
            .rolling(
                window=28,
                min_periods=28,
            )
            .mean()
        )
    )

    frame["day_of_week"] = (
        frame["sale_date"].dt.dayofweek
    )

    frame["month"] = (
        frame["sale_date"].dt.month
    )

    frame["quarter"] = (
        frame["sale_date"].dt.quarter
    )

    frame["year"] = (
        frame["sale_date"].dt.year
    )

    frame["product_id"] = (
        frame["product_id"].astype(str)
    )

    frame["category"] = (
        frame["category"].astype(str)
    )

    eligible = frame.dropna(
        subset=FEATURE_COLUMNS + ["quantity"]
    ).copy()

    if eligible.empty:
        raise ForecastingError(
            "Not enough historical data to construct "
            "forecasting features."
        )

    numeric_values = eligible[
        NUMERIC_FEATURES
    ].to_numpy(dtype=float)

    eligible = eligible.loc[
        np.isfinite(numeric_values).all(axis=1)
    ].reset_index(drop=True)

    if eligible.empty:
        raise ForecastingError(
            "No valid training rows remain "
            "after feature engineering."
        )

    return eligible


# ============================================================
# MODEL EVALUATION
# ============================================================

def calculate_regression_metrics(
    actual: Any,
    predicted: Any,
) -> dict[str, float]:

    actual_values = np.asarray(
        actual,
        dtype=float,
    ).reshape(-1)

    predicted_values = np.asarray(
        predicted,
        dtype=float,
    ).reshape(-1)

    if (
        len(actual_values) != len(predicted_values)
        or len(actual_values) < 2
    ):
        raise ForecastingError(
            "At least two aligned observations "
            "are required for evaluation."
        )

    if (
        not np.isfinite(actual_values).all()
        or not np.isfinite(predicted_values).all()
    ):
        raise ForecastingError(
            "Model evaluation produced invalid values."
        )

    predicted_values = np.maximum(
        predicted_values,
        0.0,
    )

    return {
        "mae": float(
            mean_absolute_error(
                actual_values,
                predicted_values,
            )
        ),
        "rmse": float(
            np.sqrt(
                mean_squared_error(
                    actual_values,
                    predicted_values,
                )
            )
        ),
        "r2": float(
            r2_score(
                actual_values,
                predicted_values,
            )
        ),
    }


# ============================================================
# ML PIPELINE
# ============================================================

def _make_pipeline(
    estimator: Any,
) -> Pipeline:

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES,
            ),
        ]
    )

    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("regressor", estimator),
        ]
    )


# ============================================================
# ML MODELS
# ============================================================

def _candidate_estimators() -> list[tuple[str, Any]]:

    return [
        (
            "Random Forest Regressor",
            RandomForestRegressor(
                n_estimators=200,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
        (
            "Extra Trees Regressor",
            ExtraTreesRegressor(
                n_estimators=200,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]


# ============================================================
# MODEL VERSION
# ============================================================

def _new_model_version() -> str:

    return (
        f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}"
        f"-{uuid4().hex[:8]}"
    )


# ============================================================
# TRAINING FAILURE HANDLER
# ============================================================

def _record_training_failure(
    db: Session,
    model_version: str,
    error: Exception,
    training_records: int,
    evaluation_records: int,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:

    db.rollback()

    failed_run = ModelRun(
        model_name="Training Job",
        model_version=model_version,
        prediction_target=PREDICTION_TARGET,
        training_records=training_records,
        evaluation_records=evaluation_records,
        training_status="failed",
        error_message=str(error)[:2000],
        is_active=False,
    )

    try:
        db.add(failed_run)
        db.commit()

    except Exception:
        db.rollback()

    return {
        "training_status": "failed",
        "model_version": model_version,
        "selected_model": None,
        "training_records": training_records,
        "evaluation_records": evaluation_records,
        "trained_at": datetime.now(timezone.utc),
        "candidates": candidates,
        "error_message": str(error)[:2000],
    }


# ============================================================
# TRAIN AND ACTIVATE MODEL
# ============================================================

def train_and_activate_model(
    db: Session,
    artifact_dir: Optional[Path] = None,
) -> dict[str, Any]:

    model_version = _new_model_version()

    training_records = 0
    evaluation_records = 0

    candidate_results = []

    temporary_path = None

    try:
        sales = clean_sales_history(
            load_historical_sales(db)
        )

        if len(sales) < settings.MIN_TRAINING_RECORDS:
            raise ForecastingError(
                "Insufficient training records."
            )

        if (
            sales["sale_date"].nunique()
            < settings.MIN_TRAINING_DAYS
        ):
            raise ForecastingError(
                "Insufficient distinct sales dates."
            )

        frame = build_training_frame(sales)

        training_records = len(frame)

        if (
            training_records
            < settings.MIN_TRAINING_RECORDS
        ):
            raise ForecastingError(
                "Insufficient eligible training rows."
            )

        ordered_dates = np.sort(
            frame["sale_date"].unique()
        )

        split_position = int(
            len(ordered_dates) * 0.8
        )

        if (
            split_position <= 0
            or split_position >= len(ordered_dates)
        ):
            raise ForecastingError(
                "Unable to split historical dates."
            )

        holdout_start = pd.Timestamp(
            ordered_dates[split_position]
        )

        training_rows = frame[
            frame["sale_date"] < holdout_start
        ]

        evaluation_rows = frame[
            frame["sale_date"] >= holdout_start
        ]

        evaluation_records = len(
            evaluation_rows
        )

        if (
            len(training_rows) < 20
            or evaluation_records < 2
        ):
            raise ForecastingError(
                "Insufficient training or evaluation rows."
            )

        train_features = training_rows[
            FEATURE_COLUMNS
        ]

        train_target = training_rows[
            "quantity"
        ].to_numpy(dtype=float)

        holdout_features = evaluation_rows[
            FEATURE_COLUMNS
        ]

        holdout_target = evaluation_rows[
            "quantity"
        ].to_numpy(dtype=float)

        valid_candidates = []

        # ----------------------------------------------------
        # EVALUATE CANDIDATE MODELS
        # ----------------------------------------------------

        for model_name, estimator in _candidate_estimators():

            try:
                pipeline = _make_pipeline(
                    estimator
                )

                pipeline.fit(
                    train_features,
                    train_target,
                )

                predictions = pipeline.predict(
                    holdout_features
                )

                metrics = calculate_regression_metrics(
                    holdout_target,
                    predictions,
                )

                result = {
                    "model_name": model_name,
                    **metrics,
                    "training_status": "evaluated",
                    "error_message": None,
                }

                candidate_results.append(result)

                valid_candidates.append(
                    {
                        "model_name": model_name,
                        "estimator": estimator,
                        **metrics,
                    }
                )

            except Exception as error:
                candidate_results.append(
                    {
                        "model_name": model_name,
                        "mae": None,
                        "rmse": None,
                        "r2": None,
                        "training_status": "failed",
                        "error_message": str(error)[:1000],
                    }
                )

        if not valid_candidates:
            raise ForecastingError(
                "All candidate ML models failed."
            )

        # ----------------------------------------------------
        # SELECT BEST MODEL
        # ----------------------------------------------------

        selected = min(
            valid_candidates,
            key=lambda candidate: (
                candidate["rmse"],
                candidate["mae"],
            ),
        )

        # ----------------------------------------------------
        # TRAIN FINAL MODEL
        # ----------------------------------------------------

        final_pipeline = _make_pipeline(
            clone(selected["estimator"])
        )

        final_pipeline.fit(
            frame[FEATURE_COLUMNS],
            frame["quantity"].to_numpy(dtype=float),
        )

        # ----------------------------------------------------
        # SAVE MODEL
        # ----------------------------------------------------

        output_dir = Path(
            artifact_dir
            or settings.MODEL_ARTIFACT_DIR
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifact_path = (
            output_dir
            / f"sales_forecast_{model_version}.pkl"
        )

        temporary_path = (
            output_dir
            / f".sales_forecast_{model_version}.tmp"
        )

        bundle = {
            "pipeline": final_pipeline,
            "model_name": selected["model_name"],
            "model_version": model_version,
            "prediction_target": PREDICTION_TARGET,
            "feature_columns": FEATURE_COLUMNS,
            "history_end_date": (
                sales["sale_date"]
                .max()
                .date()
                .isoformat()
            ),
        }

        joblib.dump(
            bundle,
            temporary_path,
            compress=3,
        )

        verified_bundle = joblib.load(
            temporary_path
        )

        probe = np.asarray(
            verified_bundle["pipeline"].predict(
                holdout_features.iloc[:1]
            ),
            dtype=float,
        )

        if not np.isfinite(probe).all():
            raise ForecastingError(
                "Saved model failed prediction validation."
            )

        temporary_path.replace(
            artifact_path
        )

        # ----------------------------------------------------
        # UPDATE ACTIVE MODEL IN MYSQL
        # ----------------------------------------------------

        db.query(ModelRun).filter(
            ModelRun.is_active.is_(True)
        ).update(
            {
                ModelRun.is_active: False
            },
            synchronize_session=False,
        )

        selected_run = None

        for candidate in candidate_results:

            is_selected = (
                candidate["model_name"]
                == selected["model_name"]
            )

            model_run = ModelRun(
                model_name=candidate["model_name"],
                model_version=model_version,
                prediction_target=PREDICTION_TARGET,
                training_records=training_records,
                evaluation_records=evaluation_records,
                mae=candidate["mae"],
                rmse=candidate["rmse"],
                r2=candidate["r2"],
                artifact_path=(
                    str(artifact_path)
                    if is_selected
                    else None
                ),
                is_active=is_selected,
                training_status=(
                    "succeeded"
                    if is_selected
                    else candidate["training_status"]
                ),
                error_message=candidate["error_message"],
            )

            db.add(model_run)

            if is_selected:
                selected_run = model_run

        db.flush()
        db.commit()

        db.refresh(selected_run)

        return {
            "training_status": "succeeded",
            "model_version": model_version,
            "selected_model": selected["model_name"],
            "training_records": training_records,
            "evaluation_records": evaluation_records,
            "trained_at": selected_run.trained_at,
            "candidates": candidate_results,
            "error_message": None,
        }

    except Exception as error:

        if (
            temporary_path
            and temporary_path.exists()
        ):
            temporary_path.unlink(
                missing_ok=True
            )

        return _record_training_failure(
            db,
            model_version,
            error,
            training_records,
            evaluation_records,
            candidate_results,
        )


# ============================================================
# DATE CONVERSION
# ============================================================

def _as_date(value: Any) -> date:

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return pd.Timestamp(value).date()


# ============================================================
# GENERATE FORECAST AND SAVE TO MYSQL
# ============================================================

def forecast_and_record(
    db: Session,
    product_id: int,
    user_id: int,
    forecast_date: Optional[date] = None,
    horizon_days: Optional[int] = None,
) -> PredictionHistory:

    # --------------------------------------------------------
    # LOAD ACTIVE MODEL
    # --------------------------------------------------------

    model_run = (
        db.query(ModelRun)
        .filter(
            ModelRun.is_active.is_(True),
            ModelRun.training_status == "succeeded",
        )
        .order_by(
            ModelRun.trained_at.desc()
        )
        .first()
    )

    if not model_run or not model_run.artifact_path:
        raise ForecastingError(
            "No active trained forecasting model is available."
        )

    # --------------------------------------------------------
    # VALIDATE PRODUCT
    # --------------------------------------------------------

    product = (
        db.query(Product)
        .filter(
            Product.product_id == product_id
        )
        .first()
    )

    if not product:
        raise ForecastingError(
            f"Product with ID {product_id} was not found"
        )

    # --------------------------------------------------------
    # DETERMINE FORECAST DATE
    # --------------------------------------------------------

    latest_sale_at = (
        db.query(
            func.max(Sale.sale_date)
        )
        .filter(
            Sale.quantity > 0
        )
        .scalar()
    )

    if not latest_sale_at:
        raise ForecastingError(
            "No historical sales are available."
        )

    latest_data_date = _as_date(
        latest_sale_at
    )

    if horizon_days is not None:

        if not (
            1
            <= horizon_days
            <= settings.MAX_FORECAST_HORIZON_DAYS
        ):
            raise ForecastingError(
                "Invalid forecast horizon."
            )

        target_date = (
            latest_data_date
            + timedelta(days=horizon_days)
        )

    elif forecast_date is not None:
        target_date = forecast_date

    else:
        raise ForecastingError(
            "Provide a forecast date or horizon."
        )

    actual_horizon = (
        target_date - latest_data_date
    ).days

    if not (
        1
        <= actual_horizon
        <= settings.MAX_FORECAST_HORIZON_DAYS
    ):
        raise ForecastingError(
            "Forecast date is outside the supported horizon."
        )

    # --------------------------------------------------------
    # LOAD SAVED MODEL
    # --------------------------------------------------------

    artifact_path = Path(
        model_run.artifact_path
    )

    if not artifact_path.is_file():
        raise ForecastingError(
            "Active model artifact is missing."
        )

    try:
        bundle = joblib.load(
            artifact_path
        )

    except Exception as error:
        raise ForecastingError(
            f"Unable to load model: {error}"
        ) from error

    if (
        bundle.get("model_version")
        != model_run.model_version
    ):
        raise ForecastingError(
            "Model version mismatch."
        )

    pipeline = bundle["pipeline"]

    # --------------------------------------------------------
    # LOAD PRODUCT SALES HISTORY
    # --------------------------------------------------------

    product_sales = (
        db.query(
            Sale.sale_date,
            Sale.quantity,
            Sale.unit_price,
        )
        .filter(
            Sale.product_id == product_id,
            Sale.quantity > 0,
            Sale.sale_date.is_not(None),
        )
        .order_by(
            Sale.sale_date.asc()
        )
        .all()
    )

    if not product_sales:
        raise ForecastingError(
            "This product has no historical sales."
        )

    quantity_by_date = {}
    price_numerator_by_date = {}
    price_quantity_by_date = {}

    for sale in product_sales:

        sale_day = _as_date(
            sale.sale_date
        )

        quantity = float(
            sale.quantity
        )

        unit_price = float(
            sale.unit_price or 0
        )

        quantity_by_date[sale_day] = (
            quantity_by_date.get(
                sale_day,
                0.0,
            )
            + quantity
        )

        price_numerator_by_date[sale_day] = (
            price_numerator_by_date.get(
                sale_day,
                0.0,
            )
            + unit_price * quantity
        )

        price_quantity_by_date[sale_day] = (
            price_quantity_by_date.get(
                sale_day,
                0.0,
            )
            + quantity
        )

    price_by_date = {
        sale_day: (
            price_numerator_by_date[sale_day]
            / price_quantity_by_date[sale_day]
        )
        for sale_day in price_quantity_by_date
        if price_quantity_by_date[sale_day] > 0
    }

    latest_price_date = (
        max(price_by_date)
        if price_by_date
        else None
    )

    latest_price = price_by_date.get(
        latest_price_date,
        float(product.base_price or 0),
    )

    # --------------------------------------------------------
    # PREPARE LAST 28 DAYS OF SALES
    # --------------------------------------------------------

    history_start = (
        latest_data_date
        - timedelta(days=27)
    )

    recent_quantities = [
        quantity_by_date.get(
            history_start
            + timedelta(days=day_offset),
            0.0,
        )
        for day_offset in range(28)
    ]

    # --------------------------------------------------------
    # GENERATE RECURSIVE FORECAST
    # --------------------------------------------------------

    try:

        for day_offset in range(
            1,
            actual_horizon + 1,
        ):

            current_date = (
                latest_data_date
                + timedelta(days=day_offset)
            )

            feature_row = {
                "product_id": str(product_id),
                "category": str(
                    product.category or "Unknown"
                ),
                "price": latest_price,
                "lag_1": recent_quantities[-1],
                "lag_7": recent_quantities[-7],
                "rolling_mean_7": float(
                    np.mean(
                        recent_quantities[-7:]
                    )
                ),
                "rolling_mean_28": float(
                    np.mean(
                        recent_quantities[-28:]
                    )
                ),
                "day_of_week": current_date.weekday(),
                "month": current_date.month,
                "quarter": (
                    (current_date.month - 1) // 3
                ) + 1,
                "year": current_date.year,
            }

            feature_frame = pd.DataFrame(
                [feature_row]
            )

            model_prediction = float(
                np.asarray(
                    pipeline.predict(
                        feature_frame
                    )
                ).reshape(-1)[0]
            )

            if not np.isfinite(
                model_prediction
            ):
                raise ForecastingError(
                    "ML model returned an invalid prediction."
                )

            predicted_quantity = max(
                0.0,
                model_prediction,
            )

            recent_quantities.append(
                predicted_quantity
            )

        final_prediction = Decimal(
            f"{predicted_quantity:.4f}"
        )

    except ForecastingError:
        raise

    except Exception as error:
        raise ForecastingError(
            f"ML forecasting failed: {error}"
        ) from error

    # --------------------------------------------------------
    # SAVE PREDICTION HISTORY
    # --------------------------------------------------------

    history = PredictionHistory(
        model_run_id=model_run.model_run_id,
        product_id=product_id,
        forecast_date=target_date,
        horizon_days=actual_horizon,
        predicted_quantity=final_prediction,
        model_name=model_run.model_name,
        model_version=model_run.model_version,
        user_id=user_id,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history