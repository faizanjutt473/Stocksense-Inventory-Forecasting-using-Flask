from datetime import timedelta

import numpy as np
import pandas as pd
from sqlalchemy import func

from app.extensions import db
from app.models import Sale

MODELS = ("prophet", "xgboost")
HISTORY_DAYS = 90      # model ko pichle 90 din ka data milta hai
HORIZON_DAYS = 28      # agle 4 hafte
MIN_SALE_DAYS = 10     # kam az kam itne din ki sales chahiye


class ForecastError(Exception):
    pass


def build_series(product_id):
    """Pichle 90 din ki daily sales (jis din sale nahi hui wahan 0)."""
    end = db.session.query(func.max(Sale.sale_date)).scalar()
    if end is None:
        raise ForecastError("Abhi koi sales record maujood nahi")
    start = end - timedelta(days=HISTORY_DAYS - 1)

    rows = (db.session.query(Sale.sale_date, func.sum(Sale.quantity))
            .filter(Sale.product_id == product_id, Sale.sale_date >= start)
            .group_by(Sale.sale_date)
            .all())

    series = pd.Series(0.0, index=pd.date_range(start, end, freq="D"))
    for day, qty in rows:
        series[pd.Timestamp(day)] = float(qty)

    if (series > 0).sum() < MIN_SALE_DAYS:
        raise ForecastError("Is product ki sales history bohat kam hai, forecast nahi ban sakta")
    return series


def _prophet(series, horizon):
    import logging
    logging.getLogger("cmdstanpy").disabled = True
    logging.getLogger("prophet").setLevel(logging.ERROR)
    from prophet import Prophet

    df = pd.DataFrame({"ds": series.index, "y": series.values})
    model = Prophet(yearly_seasonality=False, daily_seasonality=False, weekly_seasonality=True)
    model.fit(df)
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future).tail(horizon)
    return [max(0.0, float(v)) for v in forecast["yhat"]]


def _xgboost(series, horizon):
    from xgboost import XGBRegressor

    cols = ["dow", "lag1", "lag7", "roll7"]
    df = pd.DataFrame({"y": series})
    df["dow"] = df.index.dayofweek
    df["lag1"] = df["y"].shift(1)
    df["lag7"] = df["y"].shift(7)
    df["roll7"] = df["y"].shift(1).rolling(7).mean()
    df = df.dropna()

    model = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.08,
                         subsample=0.9, random_state=42)
    model.fit(df[cols], df["y"])

    # Ek ek din aage ka andaza, har andaza agle din ka input banta hai
    history = list(series.values)
    last_date = series.index[-1]
    preds = []
    for i in range(1, horizon + 1):
        day = last_date + timedelta(days=i)
        feats = pd.DataFrame(
            [[day.dayofweek, history[-1], history[-7], float(np.mean(history[-7:]))]],
            columns=cols,
        )
        value = max(0.0, float(model.predict(feats)[0]))
        history.append(value)
        preds.append(value)
    return preds


def _weekly(values):
    return [int(round(sum(values[i:i + 7]))) for i in range(0, len(values), 7)]


def run(product, model_name):
    series = build_series(product.id)
    if model_name == "prophet":
        preds = _prophet(series, HORIZON_DAYS)
    else:
        preds = _xgboost(series, HORIZON_DAYS)

    history_weeks = _weekly(list(series.values[-84:]))      # pichle 12 hafte
    forecast_weeks = _weekly(preds)                          # agle 4 hafte
    total = sum(forecast_weeks)

    return {
        "product": {"id": product.id, "sku": product.sku, "name": product.name},
        "model": model_name,
        "history": {"labels": [f"W{i + 1}" for i in range(12)], "units": history_weeks},
        "forecast": {"labels": [f"W{i + 13}" for i in range(4)], "units": forecast_weeks},
        "next_4_weeks_demand": total,
        "current_stock": product.stock,
        "suggested_reorder": max(total - product.stock, 0),
        "avg_daily_demand": round(total / HORIZON_DAYS, 1),
    }