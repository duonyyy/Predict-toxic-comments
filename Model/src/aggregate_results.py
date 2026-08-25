"""
Module: Model_final_v3/src/aggregate_results.py
Description: Automatically aggregates experiment outputs, generates result CSVs,
determines best models, generates report_metrics.json, and triggers publication figure generation.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"
REPORT_DIR = BASE_DIR / "report"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR = BASE_DIR / "data"
SPLITS_DIR = BASE_DIR / "data_splits"

from evaluate import run_full_length_analysis
from error_analysis import extract_error_cases
from plots import (
    plot_model_comparison,
    plot_confusion_matrix,
    plot_length_analysis,
    plot_learning_curve
)


def aggregate_all():
    print("\n=======================================================")
    print("STARTING AUTOMATED BENCHMARK AGGREGATION & REPORT METRICS")
    print("=======================================================")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    models = [
        {"key": "textcnn", "name": "TextCNN", "arch": "1D-CNN (Word Embeddings)"},
        {"key": "phobert", "name": "PhoBERT", "arch": "Pretrained RoBERTa (Monolingual)"},
        {"key": "videberta", "name": "ViDeBERTa", "arch": "Pretrained DeBERTa (Disentangled)"},
        {"key": "xlmr", "name": "XLM-R", "arch": "Pretrained RoBERTa (Multilingual)"},
    ]

    t1_records = []
    t2_records = []
    dev_records = []
    per_class_records = []

    for m in models:
        key = m["key"]
        name = m["name"]
        arch = m["arch"]

        # Check Task 1
        p1_file = RESULTS_DIR / "predictions" / f"{key}_task1.csv"
        cm1_file = RESULTS_DIR / "confusion_matrices" / f"{key}_task1_cm.csv"
        h1_file = ARTIFACTS_DIR / key / "task1" / "learning_history.csv"

        if p1_file.exists():
            df1 = pd.read_csv(p1_file, dtype="string", keep_default_na=False, encoding="utf-8-sig")
            from metrics import compute_all_metrics
            lmap = {"NON-TOXIC": 0, "TOXIC": 1}
            y_t = [lmap[x] for x in df1["gold_label"]]
            y_p = [lmap[x] for x in df1["predicted_label"]]
            res = compute_all_metrics(y_t, y_p, ["NON-TOXIC", "TOXIC"])
            m_sum = res["summary"]

            t1_records.append({
                "Model": name,
                "Architecture": arch,
                "Status": "COMPLETED",
                "Accuracy": m_sum["Accuracy"],
                "Macro_Precision": m_sum["Macro_Precision"],
                "Macro_Recall": m_sum["Macro_Recall"],
                "Macro_F1": m_sum["Macro_F1"],
                "Weighted_F1": m_sum["Weighted_F1"]
            })

            # Per class
            for _, r in res["per_class_df"].iterrows():
                per_class_records.append({
                    "task": "Task 1 (Toxicity)",
                    "model": name,
                    "label": r["class_name"],
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "f1": r["f1_score"],
                    "support": r["support"]
                })

            if h1_file.exists():
                h1_df = pd.read_csv(h1_file)
                best_h1 = h1_df.loc[h1_df["dev_macro_f1"].idxmax()]
                dev_records.append({
                    "model": name,
                    "task": "Task 1 (Toxicity)",
                    "best_epoch": int(best_h1["epoch"]),
                    "accuracy": best_h1["dev_accuracy"],
                    "macro_precision": best_h1.get("dev_macro_precision", best_h1["dev_accuracy"]),
                    "macro_recall": best_h1.get("dev_macro_recall", best_h1["dev_accuracy"]),
                    "macro_f1": best_h1["dev_macro_f1"],
                    "weighted_f1": best_h1.get("dev_weighted_f1", best_h1["dev_macro_f1"]),
                    "training_time_seconds": 0.0,
                    "checkpoint_path": f"artifacts/{key}/task1/best_model"
                })
        else:
            t1_records.append({
                "Model": name,
                "Architecture": arch,
                "Status": "PENDING (GPU Required)",
                "Accuracy": None,
                "Macro_Precision": None,
                "Macro_Recall": None,
                "Macro_F1": None,
                "Weighted_F1": None
            })

        # Check Task 2
        p2_file = RESULTS_DIR / "predictions" / f"{key}_task2.csv"
        cm2_file = RESULTS_DIR / "confusion_matrices" / f"{key}_task2_cm.csv"
        h2_file = ARTIFACTS_DIR / key / "task2" / "learning_history.csv"

        if p2_file.exists():
            df2 = pd.read_csv(p2_file, dtype="string", keep_default_na=False, encoding="utf-8-sig")
            from metrics import compute_all_metrics
            lmap2 = {"EXPLICIT": 0, "IMPLICIT": 1}
            y_t2 = [lmap2[x] for x in df2["gold_label"]]
            y_p2 = [lmap2[x] for x in df2["predicted_label"]]
            res2 = compute_all_metrics(y_t2, y_p2, ["EXPLICIT", "IMPLICIT"])
            m_sum2 = res2["summary"]

            t2_records.append({
                "Model": name,
                "Architecture": arch,
                "Status": "COMPLETED",
                "Accuracy": m_sum2["Accuracy"],
                "Macro_Precision": m_sum2["Macro_Precision"],
                "Macro_Recall": m_sum2["Macro_Recall"],
                "Macro_F1": m_sum2["Macro_F1"],
                "Weighted_F1": m_sum2["Weighted_F1"]
            })

            # Per class
            for _, r in res2["per_class_df"].iterrows():
                per_class_records.append({
                    "task": "Task 2 (Expression)",
                    "model": name,
                    "label": r["class_name"],
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "f1": r["f1_score"],
                    "support": r["support"]
                })

            if h2_file.exists():
                h2_df = pd.read_csv(h2_file)
                best_h2 = h2_df.loc[h2_df["dev_macro_f1"].idxmax()]
                dev_records.append({
                    "model": name,
                    "task": "Task 2 (Expression)",
                    "best_epoch": int(best_h2["epoch"]),
                    "accuracy": best_h2["dev_accuracy"],
                    "macro_precision": best_h2.get("dev_macro_precision", best_h2["dev_accuracy"]),
                    "macro_recall": best_h2.get("dev_macro_recall", best_h2["dev_accuracy"]),
                    "macro_f1": best_h2["dev_macro_f1"],
                    "weighted_f1": best_h2.get("dev_weighted_f1", best_h2["dev_macro_f1"]),
                    "training_time_seconds": 0.0,
                    "checkpoint_path": f"artifacts/{key}/task2/best_model"
                })
        else:
            t2_records.append({
                "Model": name,
                "Architecture": arch,
                "Status": "PENDING (GPU Required)",
                "Accuracy": None,
                "Macro_Precision": None,
                "Macro_Recall": None,
                "Macro_F1": None,
                "Weighted_F1": None
            })

    # Save summary tables
    t1_df = pd.DataFrame(t1_records)
    t2_df = pd.DataFrame(t2_records)
    dev_df = pd.DataFrame(dev_records)
    per_class_df = pd.DataFrame(per_class_records)

    t1_df.to_csv(RESULTS_DIR / "test_results_task1.csv", index=False, encoding="utf-8-sig")
    t2_df.to_csv(RESULTS_DIR / "test_results_task2.csv", index=False, encoding="utf-8-sig")
    dev_df.to_csv(RESULTS_DIR / "dev_results.csv", index=False, encoding="utf-8-sig")
    per_class_df.to_csv(RESULTS_DIR / "per_class_metrics.csv", index=False, encoding="utf-8-sig")

    # 2. Length Analysis & Error Extraction for best available model
    completed_t1 = t1_df.dropna(subset=["Macro_F1"])
    completed_t2 = t2_df.dropna(subset=["Macro_F1"])

    best_t1_row = completed_t1.loc[completed_t1["Macro_F1"].idxmax()] if not completed_t1.empty else None
    best_t2_row = completed_t2.loc[completed_t2["Macro_F1"].idxmax()] if not completed_t2.empty else None

    best_t1_key = "textcnn"
    best_t2_key = "textcnn"
    if best_t1_row is not None:
        for m in models:
            if m["name"] == best_t1_row["Model"]:
                best_t1_key = m["key"]

    if best_t2_row is not None:
        for m in models:
            if m["name"] == best_t2_row["Model"]:
                best_t2_key = m["key"]

    len_df = run_full_length_analysis(best_t1_key)
    err_df = extract_error_cases(best_t1_key, top_k=5)

    best_t1_model = best_t1_row["Model"] if best_t1_row is not None else "TextCNN"
    best_t1_f1 = float(best_t1_row["Macro_F1"]) if best_t1_row is not None else 0.0

    best_t2_model = best_t2_row["Model"] if best_t2_row is not None else "TextCNN"
    best_t2_f1 = float(best_t2_row["Macro_F1"]) if best_t2_row is not None else 0.0

    # 3. Generate Figures
    if not completed_t1.empty:
        plot_model_comparison(completed_t1, task_name="task1", output_name="01_model_comparison_task1.png")
    if not completed_t2.empty:
        plot_model_comparison(completed_t2, task_name="task2", output_name="02_model_comparison_task2.png")

    cm1_path = RESULTS_DIR / "confusion_matrices" / f"{best_t1_key}_task1_cm.csv"
    cm2_path = RESULTS_DIR / "confusion_matrices" / f"{best_t2_key}_task2_cm.csv"
    if cm1_path.exists():
        plot_confusion_matrix(pd.read_csv(cm1_path, index_col=0), task_name="task1", output_name="03_confusion_matrix_task1_best.png", model_name=best_t1_model)
    if cm2_path.exists():
        plot_confusion_matrix(pd.read_csv(cm2_path, index_col=0), task_name="task2", output_name="04_confusion_matrix_task2_best.png", model_name=best_t2_model)

    if not len_df.empty:
        len1 = len_df[len_df["task"] == "Task 1 (Toxicity)"]
        len2 = len_df[len_df["task"] == "Task 2 (Expression)"]
        if not len1.empty:
            plot_length_analysis(len1, task_name="task1", output_name="05_length_analysis_task1.png")
        if not len2.empty:
            plot_length_analysis(len2, task_name="task2", output_name="06_length_analysis_task2.png")

    h1_path = ARTIFACTS_DIR / best_t1_key / "task1" / "training_history.csv"
    if not h1_path.exists():
        h1_path = ARTIFACTS_DIR / best_t1_key / "task1" / "learning_history.csv"

    h2_path = ARTIFACTS_DIR / best_t2_key / "task2" / "training_history.csv"
    if not h2_path.exists():
        h2_path = ARTIFACTS_DIR / best_t2_key / "task2" / "learning_history.csv"

    if h1_path.exists():
        plot_learning_curve(h1_path, task_name="task1", output_name="07_learning_curve_task1_best.png", model_name=best_t1_model)
    if h2_path.exists():
        plot_learning_curve(h2_path, task_name="task2", output_name="08_learning_curve_task2_best.png", model_name=best_t2_model)

    # 4. Build report_metrics.json
    gold_df = pd.read_csv(DATA_DIR / "gold_standard_final_48670.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    train_df = pd.read_csv(SPLITS_DIR / "train.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    dev_split_df = pd.read_csv(SPLITS_DIR / "dev.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    test_split_df = pd.read_csv(SPLITS_DIR / "test.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")

    report_metrics = {
        "dataset_summary": {
            "total_samples": len(gold_df),
            "toxicity_distribution": {
                "NON-TOXIC": int((gold_df["toxicity"] == "NON-TOXIC").sum()),
                "TOXIC": int((gold_df["toxicity"] == "TOXIC").sum())
            },
            "expression_type_distribution": {
                "EXPLICIT": int((gold_df["expression_type"] == "EXPLICIT").sum()),
                "IMPLICIT": int((gold_df["expression_type"] == "IMPLICIT").sum())
            }
        },
        "split_summary": {
            "train_count": len(train_df),
            "dev_count": len(dev_split_df),
            "test_count": len(test_split_df),
            "train_toxic": int((train_df["toxicity"] == "TOXIC").sum()),
            "dev_toxic": int((dev_split_df["toxicity"] == "TOXIC").sum()),
            "test_toxic": int((test_split_df["toxicity"] == "TOXIC").sum())
        },
        "best_models": {
            "task1": {
                "model": best_t1_model,
                "macro_f1": best_t1_f1
            },
            "task2": {
                "model": best_t2_model,
                "macro_f1": best_t2_f1
            }
        },
        "test_results_task1": t1_df.to_dict(orient="records"),
        "test_results_task2": t2_df.to_dict(orient="records"),
        "dev_results": dev_df.to_dict(orient="records"),
        "per_class_metrics": per_class_df.to_dict(orient="records")
    }

    with open(REPORT_DIR / "report_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report_metrics, f, indent=2, ensure_ascii=False)

    print("PASS: Generated report/report_metrics.json and all aggregated outputs.")


if __name__ == "__main__":
    aggregate_all()
