"""
Module: Model_final_v2/src/metrics.py
Description: Standardized scientific evaluation metrics calculation.
Calculates Accuracy, Macro-Precision, Macro-Recall, Macro-F1, Weighted-F1, per-class metrics, and confusion matrix.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


def compute_all_metrics(y_true: List[int], y_pred: List[int], target_names: List[str]) -> Dict[str, Any]:
    """Computes comprehensive evaluation metrics ensuring clear distinction between macro metrics and per-class metrics."""
    acc = accuracy_score(y_true, y_pred)
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    # Per-class metrics
    report_dict = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        output_dict=True,
        zero_division=0
    )

    per_class_list = []
    for cls_name in target_names:
        if cls_name in report_dict:
            per_class_list.append({
                "class_name": cls_name,
                "precision": round(float(report_dict[cls_name]["precision"]), 4),
                "recall": round(float(report_dict[cls_name]["recall"]), 4),
                "f1_score": round(float(report_dict[cls_name]["f1-score"]), 4),
                "support": int(report_dict[cls_name]["support"])
            })
    per_class_df = pd.DataFrame(per_class_list)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    cm_df = pd.DataFrame(
        cm,
        index=[f"Actual_{n}" for n in target_names],
        columns=[f"Pred_{n}" for n in target_names]
    )

    summary_metrics = {
        "Accuracy": round(float(acc), 4),
        "Macro_Precision": round(float(macro_p), 4),
        "Macro_Recall": round(float(macro_r), 4),
        "Macro_F1": round(float(macro_f1), 4),
        "Weighted_F1": round(float(weighted_f1), 4)
    }

    return {
        "summary": summary_metrics,
        "per_class_df": per_class_df,
        "confusion_matrix_df": cm_df
    }
