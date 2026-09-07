"""Deterministic paper graphics and LaTeX tables; never trains a model.

First run export_baselines.py once to export the unchanged fixed baseline fit.
Representative window = earliest argmin distance to median RF window MAE.
PDF creation/modification dates are omitted for deterministic vector output.
"""
from pathlib import Path
import json
import hashlib
import zipfile
import io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import fitz

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "research_v2/paper"
RESULTS = ROOT / "research_v2/results"
FIG = PAPER / "figures"
TABLES = PAPER / "tables"
NAMES = {"engine_temperature": "Engine temperature", "tyre_pressure": "Tyre pressure", "tyre_temperature": "Tyre temperature"}
COLORS = ["#bdbdbd", "#999999", "#0072B2", "#D55E00"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9,
    "axes.labelsize": 8, "legend.fontsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})

def save(fig, name):
    fig.savefig(FIG / (name+".pdf"), bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(FIG / (name+".png"), bbox_inches="tight", dpi=220)
    plt.close(fig)

def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    verification = json.loads((PAPER / "data/baseline_export_verification.json").read_text())
    for rel, digest in verification["sources"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
    df = pd.read_csv(RESULTS / "final_comparison.csv")
    bh = pd.read_csv(RESULTS / "bilstm_horizon_metrics.csv")
    rf = pd.read_csv(PAPER / "data/baseline_horizon_metrics.csv")
    manifest = {"source_commit": verification["source_commit"], "sources": verification["sources"], "figures": {}}
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.65), layout="constrained")
    labels = ["Persistence\n(last value)", "Seasonal\nnaive", "Random\nForest", "Bi-LSTM"]
    for ax, (name, title) in zip(axes, NAMES.items()):
        rows = df[df.Dataset == name]
        bars = ax.bar(range(4), rows.MAE, color=COLORS, edgecolor="black", linewidth=.6)
        for b, hatch, value in zip(bars, ["", "//", "..", "xx"], rows.MAE):
            b.set_hatch(hatch)
            ax.text(b.get_x()+b.get_width()/2, value+rows.MAE.max()*.035, f"{value:.3f}", ha="center", fontsize=7)
        ax.set(xticks=range(4), xticklabels=labels, title=title, ylabel=f"MAE ({rows.Unit.iloc[0]})", ylim=(0, rows.MAE.max()*1.22))
        ax.yaxis.grid(True, alpha=.2)
        ax.set_axisbelow(True)
    save(fig, "model_mae_comparison")
    manifest["figures"]["model_mae_comparison"] = "results/final_comparison.csv; independent physical-unit axes"

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.55), layout="constrained")
    for ax, (name, title) in zip(axes, NAMES.items()):
        for source, model, color, style, marker in [(rf,"Persistence","#666666",":","."),
                (rf,"Random Forest",COLORS[2],"-","o"), (bh,"Bi-LSTM",COLORS[3],"--","s")]:
            d = source[(source.Dataset == name) & (source.Model == model)]
            ax.plot(d["Horizon (h)"], d.MAE, label=model, color=color, linestyle=style, marker=marker, markersize=2.5)
        ax.set(title=title, xlabel="Forecast horizon (h)", ylabel=f"MAE ({d.Unit.iloc[0]})",
               xticks=[1,6,12,18,24] if name=="engine_temperature" else [3,6,12,18,24], ylim=(0,None))
        ax.grid(alpha=.2)
    axes[0].legend(loc="upper left", frameon=False)
    save(fig,"horizon_mae_comparison")
    manifest["figures"]["horizon_mae_comparison"] = "results/bilstm_horizon_metrics.csv and paper/data/baseline_horizon_metrics.csv; no aggregate approximation"

    name="engine_temperature"
    b=np.load(PAPER / "data" / name / "baseline_predictions.npz")
    n=np.load(RESULTS / name / "test_predictions.npz")
    np.testing.assert_array_equal(b["truth"],n["truth"])
    errors=np.abs(b["truth"]-b["random_forest"]).mean(axis=1)
    idx=int(np.argmin(np.abs(errors-np.median(errors))))
    meta=json.loads((RESULTS/name/"metadata.json").read_text())
    raw=pd.read_csv(ROOT / "FYP ML Training and Pipeline Code/Engine Temperature/karachi_2024_vehicle_temperature_data.csv")
    start=int(n["target_start_rows"][idx])
    selection={"rule":"earliest test window with RF MAE closest to median RF window MAE", "zero_based_test_index":idx,
        "raw_target_start_row":start,"forecast_origin":str(raw.datetime.iloc[start-1]),
        "first_target":str(raw.datetime.iloc[start]),"last_target":str(raw.datetime.iloc[start+23]),
        "median_rf_window_mae":float(np.median(errors)),"selected_rf_window_mae":float(errors[idx])}
    (PAPER/"data/representative_window.json").write_text(json.dumps(selection,indent=2)+"\n")
    fig,ax=plt.subplots(figsize=(3.45,2.35),layout="constrained")
    for values,label,color,style in [(b["truth"][idx],"Actual","black","-"),
            (b["random_forest"][idx],"Random Forest",COLORS[2],"-."),(n["prediction"][idx],"Bi-LSTM",COLORS[3],"--")]:
        ax.plot(np.arange(1,25),values,label=label,color=color,linestyle=style,linewidth=1.2)
    ax.set(xlabel="Forecast horizon (h)",ylabel="Engine temperature (°C)",xticks=[1,6,12,18,24])
    ax.legend(frameon=False,fontsize=7); ax.grid(alpha=.2)
    save(fig,"engine_24h_forecast_comparison")
    manifest["figures"]["engine_24h_forecast_comparison"]=selection
    (TABLES/"window_caption.tex").write_text(f"Forecast issued at {selection['forecast_origin']} (dataset clock); selected RF window MAE {errors[idx]:.3f} $^\\circ$C.\n")

    fig,ax=plt.subplots(figsize=(7.1,2.65)); ax.set(xlim=(0,10),ylim=(0,4)); ax.axis("off")
    boxes=[(0.1,2.9,"Vehicle sensors\nGPS · DS18B20 · BLE TPMS"),(3.5,2.9,"ESP32-S3\nAcquisition and JSON"),
        (6.9,2.9,"Telemetry / API\nHTTP POST"),(6.9,1.55,"Swift platform / data layer\nStorage and monitoring"),
        (3.5,1.55,"Forecasting service\nHistorical target → 24 h"),(0.1,1.55,"Threshold / alert logic\nConfigurable limits"),
        (0.1,.2,"Salesforce maintenance /\nservice workflow layer\nAlert → Case / Flow*"),
        (3.5,.2,"Resolution / status feedback*\nVehicle-status API"),(6.9,.2,"Dashboard\nMonitoring and status")]
    for i,(x,y,label) in enumerate(boxes):
        ax.add_patch(FancyBboxPatch((x,y),2.95,.85,boxstyle="round,pad=0.06",facecolor="#f4f4f4",edgecolor="#333333",linestyle="--" if i==6 else "-",linewidth=.8))
        ax.text(x+1.475,y+.425,label,ha="center",va="center",fontsize=8)
    for a,b in zip(boxes,boxes[1:]):
        x,y,_=a; u,v,_=b
        if y==v: p=(x+2.99,y+.425) if u>x else (x-.04,y+.425); q=(u-.07,v+.425) if u>x else (u+3.02,v+.425)
        else: p=(x+1.475,y-.04); q=(u+1.475,v+.92)
        ax.annotate("",xy=q,xytext=p,arrowprops={"arrowstyle":"->","lw":.9})
    fig.subplots_adjust(left=.01,right=.99,bottom=.02,top=.99)
    save(fig,"system_architecture")
    manifest["figures"]["system_architecture"]="Firmware, model integration script, Apex alert ingestion/status feedback; Case/Flow and resolution linkage documented only, marked *"

    # Extract original images losslessly; screenshots are evidence of interfaces only.
    z=zipfile.ZipFile(ROOT/"Documents/2_Research-Paper.docx")
    fig,axes=plt.subplots(2,1,figsize=(7.1,4.9),layout="constrained")
    for ax,file,title in zip(axes,["image7.png","image9.png"],["(a) Fleet map and monitoring interface","(b) Sensor view with configured threshold"]):
        ax.imshow(Image.open(io.BytesIO(z.read("word/media/"+file)))); ax.axis("off"); ax.set_title(title,loc="left",fontsize=9)
    save(fig,"prototype_interfaces")
    fig,ax=plt.subplots(figsize=(3.45,1.65),layout="constrained")
    ax.imshow(Image.open(io.BytesIO(z.read("word/media/image6.jpeg")))); ax.axis("off")
    save(fig,"salesforce_alert")
    manifest["figures"]["prototype_interfaces"]="Original DOCX word/media/image7.png (1908x888), image9.png (1675x672), unchanged screenshots"
    manifest["figures"]["salesforce_alert"]="Original DOCX word/media/image6.jpeg (535x211): Vehicle Alert, not Case; low resolution, higher-resolution source needed"
    source=fitz.open(ROOT/"IoT/PCB Schematic.pdf")
    out=fitz.open(); out.insert_pdf(source,from_page=0,to_page=0); out.set_metadata({}); out.save(FIG/"hardware_schematic.pdf",no_new_id=True)
    manifest["figures"]["hardware_schematic"]="IoT/PCB Schematic.pdf, first page, preserved vector source; supplementary asset"

    rows=[r"\begin{tabular}{llrrrrrrrl}",r"\toprule",r"Target & Type & Rows & Step (h) & Lookback (h) & Horizon (h) & Train & Val. & Test & Unit \\",r"\midrule"]
    for name,title in NAMES.items():
        m=json.loads((RESULTS/name/"metadata.json").read_text())
        unit="PSI" if name=="tyre_pressure" else r"$^\circ$C"
        rows.append(f"{title} & Synthetic & {m['Rows']} & {m['Sampling interval (h)']:g} & 168 & 24 & {m['Train windows']} & {m['Validation windows']} & {m['Test windows']} & {unit} "+r"\\")
    rows += [r"\bottomrule",r"\end{tabular}"]
    (TABLES/"dataset_protocol.tex").write_text("\n".join(rows)+"\n")
    rows=[r"\begin{tabular}{llrrr}",r"\toprule",r"Target (unit) & Model & MAE & RMSE & $R^2$ \\",r"\midrule"]
    for name,title in NAMES.items():
        sub=df[df.Dataset==name]
        for i,(_,r) in enumerate(sub.iterrows()):
            unit="PSI" if name=="tyre_pressure" else r"$^\circ$C"
            label=(title+" ("+unit+")") if i==0 else ""
            vals=[(r"\textbf{"+f"{r[k]:.3f}"+"}") if k in ["MAE","RMSE"] and r[k]==sub[k].min() else f"{r[k]:.3f}" for k in ["MAE","RMSE","R2"]]
            model="Seasonal naive" if str(r.Model).startswith("Seasonal") else r.Model
            rows.append(" & ".join([label,model,*vals])+r" \\")
        rows.append(r"\midrule" if name!="tyre_temperature" else r"\bottomrule")
    rows.append(r"\end{tabular}")
    (TABLES/"main_comparison.tex").write_text("\n".join(rows)+"\n")
    for rel in ["Documents/2_Research-Paper.docx","IoT/PCB Schematic.pdf"]:
        manifest["sources"][rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    (PAPER/"data/figure_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(selection,indent=2)); print("Generated figures and tables.")

if __name__=="__main__":
    main()
