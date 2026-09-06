from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "engine_temperature": {
        "path": ROOT / "FYP ML Training and Pipeline Code/Engine Temperature/karachi_2024_vehicle_temperature_data.csv",
        "time_col": "datetime",
        "target_col": "Engine_Temperature",
        "unit": "°C",
    },
    "tyre_pressure": {
        "path": ROOT / "FYP ML Training and Pipeline Code/TP_Generated/tyre_pressure_2024.csv",
        "time_col": "Date",
        "target_col": "Tyre_Pressure_PSI",
        "unit": "PSI",
    },
    "tyre_temperature": {
        "path": ROOT / "FYP ML Training and Pipeline Code/Tyre Temperature/tyre_temp_2024.csv",
        "time_col": "Date",
        "target_col": "Tyre_Temperature_C",
        "unit": "°C",
    },
}

RANDOM_STATE = 42
TRAIN_FRACTION = 0.80
LOOKBACK_HOURS = 7 * 24
FORECAST_HOURS = 24


def infer_step_hours(index: pd.DatetimeIndex) -> float:
    diffs = index.to_series().diff().dropna().dt.total_seconds() / 3600
    step = float(diffs.median())
    if step <= 0:
        raise ValueError("Could not infer a positive sampling interval.")
    return step


def steps_for_hours(hours: int, step_hours: float) -> int:
    steps = int(round(hours / step_hours))
    if not np.isclose(steps * step_hours, hours, atol=1e-6):
        raise ValueError(
            f"Requested {hours} h is not an integer multiple of the {step_hours:g} h sampling interval."
        )
    return max(1, steps)


def make_supervised(values: np.ndarray, lookback_steps: int, horizon_steps: int):
    X, y = [], []
    last_start = len(values) - lookback_steps - horizon_steps + 1
    for start in range(last_start):
        end = start + lookback_steps
        X.append(values[start:end])
        y.append(values[end:end + horizon_steps])
    return np.asarray(X), np.asarray(y)


def metrics(y_true: np.ndarray, y_pred: np.ndarray):
    yt = y_true.reshape(-1)
    yp = y_pred.reshape(-1)
    mse = mean_squared_error(yt, yp)
    return {
        "MAE": mean_absolute_error(yt, yp),
        "RMSE": float(np.sqrt(mse)),
        "R2": r2_score(yt, yp),
    }


def evaluate_dataset(name: str, cfg: dict) -> pd.DataFrame:
    from protocol import prepare
    X, y, masks, values, starts, times, metadata = prepare(name)
    horizon_steps = metadata["Horizon steps"]
    lookback_steps = metadata["Lookback steps"]
    day_steps = horizon_steps
    X_train, X_test = X[masks["train"]], X[masks["test"]]
    y_train, y_test = y[masks["train"]], y[masks["test"]]

    # Baseline 1: repeat the most recent observed value across the full horizon.
    persistence = np.repeat(X_test[:, -1][:, None], horizon_steps, axis=1)

    # Baseline 2: repeat the same clock-time pattern from the previous day.
    if lookback_steps < day_steps:
        raise ValueError("Lookback window must contain at least one day for seasonal-naive baseline.")
    previous_day = X_test[:, -day_steps:]
    if horizon_steps <= day_steps:
        seasonal_naive = previous_day[:, :horizon_steps]
    else:
        repeats = int(np.ceil(horizon_steps / day_steps))
        seasonal_naive = np.tile(previous_day, (1, repeats))[:, :horizon_steps]

    # Baseline 3: nonlinear autoregressive model using only past target values.
    # This is intentionally simple so the Bi-LSTM must beat a credible, reproducible baseline.
    rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=16,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    rows = []
    for model_name, pred in [
        ("Persistence", persistence),
        ("Seasonal naive (previous 24 h)", seasonal_naive),
        ("Random Forest", rf_pred),
    ]:
        row = {"Dataset": name, "Model": model_name, **metrics(y_test, pred)}
        row.update(metadata)
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    outputs = []
    for name, cfg in DATASETS.items():
        print(f"Evaluating {name} from {cfg['path']} ...")
        outputs.append(evaluate_dataset(name, cfg))

    results = pd.concat(outputs, ignore_index=True)
    out_dir = ROOT / "research_v2/results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "baseline_metrics.csv"
    results.to_csv(out_file, index=False)

    print("\nBaseline results")
    print(results.to_string(index=False))
    print(f"\nSaved to: {out_file}")


if __name__ == "__main__":
    main()
