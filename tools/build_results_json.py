"""Build data/results.json from the aggregated results of the MaldiSuite-paper repository.

Usage:
    python tools/build_results_json.py [PATH_TO_MaldiSuite-paper]

The path defaults to ../MaldiSuite-paper next to this repository. Only the
standard library is needed.
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "MaldiSuite-paper"
OUT = ROOT / "data" / "results.json"

CLASSIFIERS = [
    ("mlp_attn", "MLP + attention"),
    ("cnn", "1-D CNN"),
    ("resnet", "ResNet"),
    ("transformer", "1-D ViT"),
    ("ensemble_mlp_cnn", "Ensemble (MLP + CNN)"),
]
SITES = ["DRIAMS-A", "DRIAMS-B", "DRIAMS-C", "DRIAMS-D"]
TASKS = [
    ("Staphylococcus aureus", "oxacillin"),
    ("Escherichia coli", "ceftriaxone"),
    ("Klebsiella pneumoniae", "ceftriaxone"),
]
EXPERIMENTS = [
    ("exp3_multi_species", "E. coli + K. pneumoniae", "ceftriaxone, species protected"),
    ("exp1_saureus", "S. aureus", "oxacillin"),
    ("exp1_ecoli", "E. coli", "ceftriaxone"),
    ("exp1_kpneumoniae", "K. pneumoniae", "ceftriaxone"),
]
BATCH_METRICS = ["kbet_acceptance", "lisi_batch_normalized", "species_preservation"]


def num(value):
    return round(float(value), 3) if value not in ("", None) else None


def classification():
    rows = list(csv.DictReader(open(PAPER / "results" / "classification" / "summary.csv")))
    tasks = []
    for species, drug in TASKS:
        cells = {}
        for row in rows:
            if row["species"] != species or row["drug"] != drug:
                continue
            cells.setdefault(row["site"], {})[row["classifier"]] = {
                "auroc": num(row["auroc_mean"]),
                "aurocSd": num(row["auroc_std"]),
                "balancedAccuracy": num(row["balanced_accuracy_mean"]),
                "mcc": num(row["mcc_mean"]),
                "vme": num(row["vme_mean"]),
                "me": num(row["me_mean"]),
                "fits": int(row["n_fits"]),
            }
        tasks.append({"species": species, "drug": drug, "cells": cells})
    return {
        "sites": SITES,
        "classifiers": [{"id": cid, "label": label} for cid, label in CLASSIFIERS],
        "tasks": tasks,
    }


def batch_correction():
    rows = list(csv.DictReader(open(PAPER / "results" / "batch_correction" / "supp_table_s3.csv")))
    experiments = []
    for key, title, detail in EXPERIMENTS:
        methods = []
        for row in rows:
            if row["experiment"] != key:
                continue
            methods.append({
                "id": row["method"],
                "label": row["method_display"],
                "uncorrected": row["stage"] == "pre",
                **{metric: num(row[metric]) for metric in BATCH_METRICS},
            })
        experiments.append({"id": key, "title": title, "detail": detail, "methods": methods})
    return {"experiments": experiments}


def main():
    data = {
        "source": "https://github.com/EttoreRocchi/MaldiSuite-paper",
        "classification": classification(),
        "batchCorrection": batch_correction(),
    }
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
