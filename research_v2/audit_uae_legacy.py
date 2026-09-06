"""Evaluate the older UAE artifact using an explicit in-memory Keras config migration."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import ast
import json
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from baseline_evaluation import ROOT, metrics


def migrate(config):
    if isinstance(config, list):
        return [migrate(x) for x in config]
    if not isinstance(config, dict):
        return config
    result = {k: migrate(v) for k,v in config.items()}
    if result.get("class_name") == "LSTM":
        # False is the current batch-major layout; no tensor transpose is introduced.
        if result["config"].pop("time_major",False):
            raise ValueError("Cannot migrate time-major input implicitly")
    if result.get("class_name") == "BatchNormalization" and isinstance(result["config"]["axis"],list):
        if len(result["config"]["axis"]) != 1:
            raise ValueError("Cannot migrate multi-axis normalization implicitly")
        result["config"]["axis"] = result["config"]["axis"][0]
    if isinstance(result.get("config"),dict) and "batch_input_shape" in result["config"]:
        shape = result["config"].pop("batch_input_shape")
        if result.get("class_name") == "InputLayer":
            result["config"]["batch_shape"] = shape
    return result


def main():
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    folder=ROOT/"FYP ML Training and Pipeline Code/Engine Temperature"
    nb=json.loads((folder/"Training_LSTM.ipynb").read_text(encoding="utf-8"))
    namespace={"np":np,"pd":pd}
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node,ast.FunctionDef) and node.name=="create_features":
                exec(compile(ast.Module(body=[node],type_ignores=[]),"Training_LSTM.ipynb","exec"),namespace)
    df=pd.read_csv(folder/"vehicle_engine_temperature_UAE_Vehicle0018.csv")
    df.index=pd.to_datetime(df.pop("Timestamp"))
    df["Hour"]=df.index.hour
    df["DayOfWeek"]=df.index.dayofweek
    df["Month"]=df.index.month
    df["isWeekend"]=(df.index.dayofweek>=5).astype(int)
    df["isRushHour"]=[int(7<=h<=9 or 17<=h<=19) for h in df.index.hour]
    df=namespace["create_features"](df)
    features=["Engine_Temperature_C","isWeekend","isRushHour","hour_sin","hour_cos","day_sin","day_cos","month_sin","month_cos","temp_lag_24h","temp_rolling_avg_3d"]
    split=int(len(df)*.8)
    scaler=MinMaxScaler().fit(df[features].iloc[:split])
    test=scaler.transform(df[features].iloc[split:])
    lookback,horizon=40,24
    X=np.array([test[i:i+lookback] for i in range(len(test)-lookback-horizon)])
    y=np.array([test[i+lookback:i+lookback+horizon,0] for i in range(len(test)-lookback-horizon)])
    model_path=folder/"final_model.h5"
    with h5py.File(model_path) as f:
        cfg=json.loads(f.attrs["model_config"])
    model=tf.keras.Sequential.from_config(migrate(cfg)["config"])
    model.load_weights(model_path)
    pred=model.predict(X,batch_size=64,verbose=0)
    yt=(y-scaler.min_[0])/scaler.scale_[0]
    yp=(pred-scaler.min_[0])/scaler.scale_[0]
    stored=.1794579178094864
    row={"Dataset":"UAE engine (legacy, not benchmark)","Model":str(model_path),
         "Normalized MAE stored":stored,"Normalized MAE reproduced":metrics(y,pred)["MAE"],
         "Target range":float(scaler.data_range_[0]),"Stored MAE algebraic physical conversion":stored*scaler.data_range_[0],
         "Physical metrics":metrics(yt,yp),"Unit":"degrees Celsius","Test windows":len(y),
         "Train/test timestamp intersection":len(set(df.index[:split])&set(df.index[split:])),
         "Compatibility changes":["removed time_major=False (batch-major unchanged)","singleton BatchNormalization axis list to scalar",
                                  "InputLayer batch_input_shape renamed batch_shape; redundant layer shape keys removed"],
         "Original files modified":False}
    (ROOT/"research_v2/results/uae_legacy_audit.json").write_text(json.dumps(row,indent=2),encoding="utf-8")
    print(json.dumps(row,indent=2))

if __name__ == "__main__":
    main()
