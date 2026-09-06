"""Read notebook evidence and reproduce legacy saved-model evaluation separately."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import ast
import json
import pickle
import sys
import h5py
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from baseline_evaluation import ROOT, DATASETS, metrics

def main():
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    out = ROOT / "research_v2/results"
    out.mkdir(exist_ok=True)
    evidence = []
    base = ROOT / "FYP ML Training and Pipeline Code"
    for folder in ["Engine Temperature", "TP_Generated", "Tyre Temperature", "Tyre Pressure"]:
        for path in sorted((base / folder).glob("*.ipynb")):
            if not any(s in path.name.lower() for s in ["training", "testing", "generat"]):
                continue
            nb = json.loads(path.read_text(encoding="utf-8"))
            for i, cell in enumerate(nb["cells"]):
                if cell["cell_type"] != "code":
                    continue
                source = "".join(cell["source"])
                outputs = []
                for o in cell.get("outputs", []):
                    if "text" in o:
                        outputs.append("".join(o["text"]))
                evidence.append({"notebook": str(path.relative_to(ROOT)), "cell_zero_based": i,
                                 "source": source, "text_outputs": outputs})
    (out / "notebook_evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    specs = [("engine_temperature", "Training_LSTM_Karachi.ipynb", "Final_Temp_Prediction_Model.h5", "scaler.pkl", .8, 168, 24),
             ("tyre_pressure", "Training_LSTM_TP.ipynb", "Final_TP_Prediction_Model.h5", "scaler_TP.pkl", .1, 56, 8),
             ("tyre_temperature", "Training_LSTM_Tyre_Temp.ipynb", "Final_Tyre_Temp_Prediction_Model.h5", "scaler_TTemp.pkl", .1, 56, 8)]
    results = []
    for name, notebook, model_file, scaler_file, fraction, lookback, horizon in specs:
        cfg = DATASETS[name]
        folder = cfg["path"].parent
        nb = json.loads((folder / notebook).read_text(encoding="utf-8"))
        namespace = {"np": np, "pd": pd}
        # Reconstruct only the inspected feature function, never run notebook cells wholesale.
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            tree = ast.parse("".join(cell["source"]))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == "create_features":
                    exec(compile(ast.Module(body=[node], type_ignores=[]), notebook, "exec"), namespace)
        df = pd.read_csv(cfg["path"])
        df.index = pd.to_datetime(df.pop(cfg["time_col"]))
        df = namespace["create_features"](df)
        lag = "temp" if name == "engine_temperature" else "tp"
        features = [cfg["target_col"], "isWeekend", "isRushHour", "hour_sin", "hour_cos",
                    "day_sin", "day_cos", "month_sin", "month_cos", lag+"_lag_24h", lag+"_rolling_avg_3d"]
        split = int(len(df)*fraction)
        rebuilt = MinMaxScaler().fit(df[features].iloc[:split])
        with (folder/scaler_file).open("rb") as f:
            saved = pickle.load(f)
        row = {"Dataset": name, "Notebook": notebook, "Training fraction": fraction,
               "Saved scaler matches reconstructed": bool(np.allclose(saved.scale_, rebuilt.scale_) and np.allclose(saved.min_, rebuilt.min_)),
               "Saved scaler feature names": list(getattr(saved, "feature_names_in_", [])),
               "Reconstructed target range": float(rebuilt.data_range_[0]),
               "Saved target range": float(saved.data_range_[0]),
               "Legacy test first raw timestamp": str(df.index[split+lookback])}
        with h5py.File(folder/model_file) as f:
            layers = json.loads(f.attrs["model_config"])["config"]["layers"]
            row["Saved input config"] = layers[0]["config"]
            row["Saved output steps"] = layers[-1]["config"]["units"]
        scaled = saved.transform(df[features].iloc[split:])
        # Match legacy exclusive endpoint exactly, including its omitted final window.
        X = np.array([scaled[i:i+lookback] for i in range(len(scaled)-lookback-horizon)])
        y = np.array([scaled[i+lookback:i+lookback+horizon,0] for i in range(len(scaled)-lookback-horizon)])
        try:
            model = tf.keras.models.load_model(folder/model_file, compile=False)
            pred = model.predict(X, batch_size=64, verbose=0)
            row["Reproduced normalized MAE"] = metrics(y, pred)["MAE"]
            yt = (y-saved.min_[0])/saved.scale_[0]
            yp = (pred-saved.min_[0])/saved.scale_[0]
            row.update({"Physical "+k: v for k,v in metrics(yt,yp).items()})
            row["Unit"] = cfg["unit"]
            row["Legacy test windows"] = len(y)
        except Exception as exc:
            row["Evaluation error"] = str(exc)
        results.append(row)
        print(json.dumps(row, default=str), flush=True)
    (out / "legacy_model_audit.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

if __name__ == "__main__":
    main()
