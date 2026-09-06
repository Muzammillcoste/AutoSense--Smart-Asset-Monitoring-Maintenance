"""Reproduce inspected synthetic generators in memory without plots or file writes."""
import ast
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from baseline_evaluation import DATASETS

def main():
    rows = []
    for name, notebook, variable in [("engine_temperature", "Generating Data.ipynb", "df"),
                                     ("tyre_pressure", "Generating_Data.ipynb", "df"),
                                     ("tyre_temperature", "generating_data.ipynb", "df_temp")]:
        cfg = DATASETS[name]
        path = cfg["path"].parent / notebook
        nb = json.loads(path.read_text(encoding="utf-8"))
        namespace = {"np": np, "pd": pd, "datetime": datetime, "timedelta": timedelta}
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            nodes = []
            for node in ast.parse(source).body:
                # The inspected generators use top-level plotting/file writes only.
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
                    if isinstance(node, ast.Expr) and ast.unparse(node).startswith("np.random.seed("):
                        nodes.append(node)
                    continue
                nodes.append(node)
            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
        generated = namespace[variable]
        original = pd.read_csv(cfg["path"])
        same_times = pd.DatetimeIndex(pd.to_datetime(original[cfg["time_col"]])).equals(
            pd.DatetimeIndex(pd.to_datetime(generated[cfg["time_col"]])))
        delta = np.max(np.abs(original[cfg["target_col"]].to_numpy()-generated[cfg["target_col"]].to_numpy()))
        matched = bool(same_times and np.allclose(original[cfg["target_col"]], generated[cfg["target_col"]], rtol=0, atol=1e-10))
        rows.append({"Dataset":name,"Generator":str(path),"Rows":len(original),"Timestamps match":same_times,
                     "Max absolute value difference":float(delta),"Reproduced":matched})
    output = Path(__file__).resolve().parent / "results/generator_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    if not all(row["Reproduced"] for row in rows):
        raise SystemExit("A generator does not reproduce the local dataset")

if __name__ == "__main__":
    main()
