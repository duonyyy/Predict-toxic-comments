"""
Module: Model_final_v2/src/evaluate.py
Description: Evaluates predictions across whitespace-separated token length groups on the locked Test set.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "results"

from sklearn.metrics import f1_score
from sklearn.utils import resample
from metrics import compute_all_metrics


def compute_length_analysis(pred_csv_path: Path, task_name="task1") -> pd.DataFrame:
    """Groups Test set predictions by whitespace-separated token counts and computes performance metrics."""
    df = pd.read_csv(pred_csv_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
    df["token_count"] = df["comment"].apply(lambda x: len(str(x).split()))

    if task_name == "task1":
        label_map = {"NON-TOXIC": 0, "TOXIC": 1}
        target_names = ["NON-TOXIC", "TOXIC"]
    else:
        label_map = {"EXPLICIT": 0, "IMPLICIT": 1}
        target_names = ["EXPLICIT", "IMPLICIT"]

    bins = [0, 4, 9, 16, 30, float("inf")]
    labels = [
        "Very Short (1-4)",
        "Short (5-9)",
        "Medium (10-16)",
        "Long (17-30)",
        "Very Long (>30)"
    ]
    df["length_group"] = pd.cut(df["token_count"], bins=bins, labels=labels, right=True)

    records = []
    total_samples = len(df)

    for grp_name in labels:
        grp_df = df[df["length_group"] == grp_name]
        support = len(grp_df)
        if support == 0:
            continue

        pct = round((support / total_samples) * 100, 2)
        y_true = [label_map[l] for l in grp_df["gold_label"]]
        y_pred = [label_map[l] for l in grp_df["predicted_label"]]

        eval_res = compute_all_metrics(y_true, y_pred, target_names)
        m = eval_res["summary"]

        records.append({
            "length_group": grp_name,
            "support": support,
            "percentage": pct,
            "accuracy": m["Accuracy"],
            "macro_f1": m["Macro_F1"],
            "macro_precision": m["Macro_Precision"],
            "macro_recall": m["Macro_Recall"],
            "task": "Task 1 (Toxicity)" if task_name == "task1" else "Task 2 (Expression)"
        })

    return pd.DataFrame(records)


def compute_boundary_shift(pred_csv_path: Path, model_key: str):
    """
    Extracts false positives and false negatives for Task 2 (EXPLICIT vs IMPLICIT)
    to analyze the 'boundary shift' or where the model fails to capture implicit meaning.
    Saves the errors to results/boundary_errors_{model_key}.csv.
    """
    if not pred_csv_path.exists():
        return

    df = pd.read_csv(pred_csv_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
    
    # FP: Predicted IMPLICIT, but truth is EXPLICIT
    # FN: Predicted EXPLICIT, but truth is IMPLICIT
    # We define IMPLICIT as the positive class for this boundary analysis (since it's harder)
    
    errors = df[df["predicted_label"] != df["gold_label"]].copy()
    errors["error_type"] = errors.apply(
        lambda row: "False IMPLICIT (was EXPLICIT)" if row["predicted_label"] == "IMPLICIT" else "False EXPLICIT (was IMPLICIT)", 
        axis=1
    )
    
    out_path = RESULTS_DIR / f"boundary_errors_{model_key}_task2.csv"
    errors.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"PASS: Saved boundary errors to {out_path.name} ({len(errors)} cases)")
    return errors


def compute_bootstrap_significance(csv_a: Path, csv_b: Path, task_name="task2", n_iterations=1000):
    """
    Performs bootstrap resampling to compare F1-Macro of two models.
    """
    if not csv_a.exists() or not csv_b.exists():
        return None
        
    df_a = pd.read_csv(csv_a, dtype="string", keep_default_na=False)
    df_b = pd.read_csv(csv_b, dtype="string", keep_default_na=False)
    
    if len(df_a) != len(df_b):
        print("Warning: CSVs have different lengths, cannot bootstrap properly.")
        return None
        
    y_true = df_a["gold_label"].values
    y_pred_a = df_a["predicted_label"].values
    y_pred_b = df_b["predicted_label"].values
    
    diffs = []
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    indices = np.arange(len(y_true))
    for i in range(n_iterations):
        sample_idx = resample(indices)
        
        f1_a = f1_score(y_true[sample_idx], y_pred_a[sample_idx], average="macro")
        f1_b = f1_score(y_true[sample_idx], y_pred_b[sample_idx], average="macro")
        diffs.append(f1_b - f1_a)
        
    diffs = np.array(diffs)
    
    # 95% Confidence Interval
    ci_lower = np.percentile(diffs, 2.5)
    ci_upper = np.percentile(diffs, 97.5)
    mean_diff = np.mean(diffs)
    
    # p-value: proportion of times Model B was not better than Model A (assuming B is expected to be better)
    p_value = np.mean(diffs <= 0)
    
    print(f"Bootstrap Analysis ({task_name}): Model B vs Model A")
    print(f"  Mean F1-Macro Diff: {mean_diff:.4f}")
    print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"  p-value: {p_value:.4f}")
    
    return {
        "mean_diff": mean_diff,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_value": p_value
    }


def run_full_length_analysis(model_key="textcnn"):
    p1 = RESULTS_DIR / "predictions" / f"{model_key}_task1.csv"
    p2 = RESULTS_DIR / "predictions" / f"{model_key}_task2.csv"

    dfs = []
    if p1.exists():
        dfs.append(compute_length_analysis(p1, task_name="task1"))
    if p2.exists():
        dfs.append(compute_length_analysis(p2, task_name="task2"))

    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        out_path = RESULTS_DIR / "length_analysis.csv"
        combined.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"PASS: Saved results/length_analysis.csv ({len(combined)} rows)")
        return combined
    return pd.DataFrame()


def run_advanced_evaluation(model_key="textcnn"):
    """Runs all evaluations including boundary analysis."""
    print(f"--- Running Advanced Evaluation for {model_key} ---")
    run_full_length_analysis(model_key)
    
    p2 = RESULTS_DIR / "predictions" / f"{model_key}_task2.csv"
    if p2.exists():
        compute_boundary_shift(p2, model_key)



if __name__ == "__main__":
    run_advanced_evaluation("textcnn")

