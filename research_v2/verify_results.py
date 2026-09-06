"""Verify persisted forecasts, aligned comparisons, horizon metrics and model reloads."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf
from baseline_evaluation import DATASETS, metrics
from protocol import prepare

def main():
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    out = Path(__file__).resolve().parent / "results"
    comparison = pd.read_csv(out/"final_comparison.csv")
    horizons = pd.read_csv(out/"bilstm_horizon_metrics.csv")
    assert len(comparison) == 12 and not comparison.duplicated(["Dataset","Model"]).any()
    checks = []
    for name in DATASETS:
        X,y,masks,values,starts,times,meta = prepare(name)
        group = comparison[comparison.Dataset == name]
        assert len(group) == 4
        for col in ["Protocol", "SHA256", "Train windows", "Test windows", "Train first target", "Train last target", "Test first target", "Test last target"]:
            assert group[col].nunique() == 1 and group[col].iloc[0] == meta[col], (name,col)
        saved = np.load(out/name/"test_predictions.npz")
        truth, pred = saved["truth"], saved["prediction"]
        assert truth.shape == pred.shape == y[masks["test"]].shape
        assert np.isfinite(pred).all()
        np.testing.assert_array_equal(truth, y[masks["test"]])
        np.testing.assert_array_equal(saved["target_start_rows"], starts[masks["test"]])
        row = group[group.Model == "Bi-LSTM"].iloc[0]
        for metric,value in metrics(truth,pred).items():
            np.testing.assert_allclose(row[metric],value, rtol=1e-10)
        hr = horizons[horizons.Dataset == name].sort_values("Horizon (h)")
        assert len(hr) == y.shape[1]
        for h in range(y.shape[1]):
            assert hr.iloc[h]["Horizon (h)"] == (h+1)*meta["Sampling interval (h)"]
            for metric,value in metrics(truth[:,h],pred[:,h]).items():
                np.testing.assert_allclose(hr.iloc[h][metric],value,rtol=1e-10)
        scale = np.load(out/name/"scaler.npz")
        model = tf.keras.models.load_model(out/name/"model.keras", compile=False)
        xs = (X[masks["test"]][:3]*scale["scale"]+scale["min"]).astype("float32")[...,None]
        reproduced = (model.predict(xs,verbose=0)-scale["min"])/scale["scale"]
        np.testing.assert_allclose(reproduced,pred[:3],rtol=1e-5,atol=1e-4)
        checks.append({"Comparison SHA256": hashlib.sha256((out/"final_comparison.csv").read_bytes()).hexdigest(),"Dataset":name,"Windows":len(truth),"Aggregate and horizon metrics verified":True,
                       "Split alignment verified":True,"Model reload verified":True})
    (out/"verification.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    print(json.dumps(checks,indent=2))

if __name__ == "__main__":
    main()
