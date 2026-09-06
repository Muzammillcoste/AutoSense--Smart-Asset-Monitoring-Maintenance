"""Scientific checks: forecast alignment, disjoint labels and strict cadence."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from baseline_evaluation import DATASETS, make_supervised, metrics
from protocol import prepare

class ProtocolTests(unittest.TestCase):
    def test_clock_horizons_and_disjoint_labels(self):
        for name in DATASETS:
            X, y, masks, values, starts, times, meta = prepare(name)
            self.assertEqual(meta["Lookback steps"], 168 if name == "engine_temperature" else 56)
            self.assertEqual(meta["Horizon steps"], 24 if name == "engine_temperature" else 8)
            h = y.shape[1]
            for left, right in [("train", "validation"), ("validation", "test")]:
                self.assertLess(starts[masks[left]][-1]+h-1, starts[masks[right]][0])
            for key in masks:
                i = np.flatnonzero(masks[key])[0]
                np.testing.assert_array_equal(X[i], values[starts[i]-X.shape[1]:starts[i]])
                np.testing.assert_array_equal(y[i], values[starts[i]:starts[i]+h])
                self.assertEqual((times[starts[i]+h-1]-times[starts[i]-1]).total_seconds()/3600, 24)
            self.assertEqual(starts[masks["test"]][0], int(len(values)*.8))
            self.assertEqual(starts[-1]+h, len(values))

    def test_rejects_irregular_duplicate_unsorted_and_missing_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"series.csv"
            good = pd.DataFrame({"time": pd.date_range("2024-01-01", periods=1000, freq="h"), "value": np.arange(1000.)})
            cases = [good.drop(index=500), good.copy(), good.iloc[::-1], good.copy()]
            cases[1].loc[500,"time"] = cases[1].loc[499,"time"]
            cases[3].loc[500,"value"] = np.nan
            for df in cases:
                df.to_csv(path,index=False)
                with patch.dict(DATASETS, {"fixture": {"path": path,"time_col":"time","target_col":"value","unit":"test"}}):
                    with self.assertRaises(ValueError):
                        prepare("fixture")

    def test_inverse_scaled_metrics_have_physical_units(self):
        scaler = MinMaxScaler().fit(np.array([[20.],[70.]]))
        truth = np.array([[30.,40.],[50.,60.]])
        scaled = scaler.transform(truth.reshape(-1,1)).reshape(truth.shape)
        pred = scaler.inverse_transform((scaled+.1).reshape(-1,1)).reshape(truth.shape)
        self.assertAlmostEqual(metrics(truth,pred)["MAE"],5.)
        self.assertAlmostEqual(metrics(truth,pred)["RMSE"],5.)

    def test_original_window_split_leakage_is_demonstrated(self):
        for name in DATASETS:
            X,y,masks,values,starts,times,meta = prepare(name)
            split = int(len(X)*.8)
            last_train_labels = set(range(starts[split-1], starts[split-1]+y.shape[1]))
            first_test_labels = set(range(starts[split], starts[split]+y.shape[1]))
            self.assertEqual(len(last_train_labels & first_test_labels), y.shape[1]-1)

if __name__ == "__main__":
    unittest.main()
