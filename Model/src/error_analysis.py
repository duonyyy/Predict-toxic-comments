"""
Module: Model_final_v3/src/error_analysis.py
Description: Extracts authentic qualitative error cases directly from Test set predictions for error inspection.
Strictly avoids automated rule-template hallucinations (no fabricated reasons).
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
PREDS_DIR = RESULTS_DIR / "predictions"


def extract_error_cases(model_key="textcnn", top_k=5) -> pd.DataFrame:
    """
    Extracts top false positive, false negative, and expression misclassification cases directly from Test predictions.
    Evidence is extracted strictly for post-hoc qualitative inspection.
    """
    gold_df = pd.read_csv(DATA_DIR / "gold_standard_final_48670.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    gold_map = dict(zip(gold_df["row_id"], gold_df["evidence"]))

    records = []

    # 1. Task 1 Error Cases (NON-TOXIC vs TOXIC)
    p1_path = PREDS_DIR / f"{model_key}_task1.csv"
    if p1_path.exists():
        df1 = pd.read_csv(p1_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
        df1["prob_class_1"] = df1["prob_class_1"].astype(float)
        df1["prob_class_0"] = df1["prob_class_0"].astype(float)

        # False Positive (NON-TOXIC -> TOXIC)
        fp_df = df1[(df1["gold_label"] == "NON-TOXIC") & (df1["predicted_label"] == "TOXIC")].copy()
        fp_df.sort_values(by="prob_class_1", ascending=False, inplace=True)
        for _, row in fp_df.head(top_k).iterrows():
            records.append({
                "task": "Task 1 (Toxicity)",
                "model": model_key,
                "error_type": "False Positive (NON-TOXIC -> TOXIC)",
                "row_id": row["row_id"],
                "comment": row["comment"],
                "gold_label": row["gold_label"],
                "predicted_label": row["predicted_label"],
                "confidence": row["prob_class_1"],
                "gold_evidence": gold_map.get(row["row_id"], ""),
                "analysis": ""
            })

        # False Negative (TOXIC -> NON-TOXIC)
        fn_df = df1[(df1["gold_label"] == "TOXIC") & (df1["predicted_label"] == "NON-TOXIC")].copy()
        fn_df.sort_values(by="prob_class_0", ascending=False, inplace=True)
        for _, row in fn_df.head(top_k).iterrows():
            records.append({
                "task": "Task 1 (Toxicity)",
                "model": model_key,
                "error_type": "False Negative (TOXIC -> NON-TOXIC)",
                "row_id": row["row_id"],
                "comment": row["comment"],
                "gold_label": row["gold_label"],
                "predicted_label": row["predicted_label"],
                "confidence": row["prob_class_0"],
                "gold_evidence": gold_map.get(row["row_id"], ""),
                "analysis": ""
            })

    # 2. Task 2 Error Cases (EXPLICIT vs IMPLICIT)
    p2_path = PREDS_DIR / f"{model_key}_task2.csv"
    if p2_path.exists():
        df2 = pd.read_csv(p2_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")
        df2["prob_class_1"] = df2["prob_class_1"].astype(float)
        df2["prob_class_0"] = df2["prob_class_0"].astype(float)

        # EXPLICIT -> IMPLICIT
        e2i_df = df2[(df2["gold_label"] == "EXPLICIT") & (df2["predicted_label"] == "IMPLICIT")].copy()
        e2i_df.sort_values(by="prob_class_1", ascending=False, inplace=True)
        for _, row in e2i_df.head(top_k).iterrows():
            records.append({
                "task": "Task 2 (Expression)",
                "model": model_key,
                "error_type": "Misclassification (EXPLICIT -> IMPLICIT)",
                "row_id": row["row_id"],
                "comment": row["comment"],
                "gold_label": row["gold_label"],
                "predicted_label": row["predicted_label"],
                "confidence": row["prob_class_1"],
                "gold_evidence": gold_map.get(row["row_id"], ""),
                "analysis": ""
            })

        # IMPLICIT -> EXPLICIT
        i2e_df = df2[(df2["gold_label"] == "IMPLICIT") & (df2["predicted_label"] == "EXPLICIT")].copy()
        i2e_df.sort_values(by="prob_class_0", ascending=False, inplace=True)
        for _, row in i2e_df.head(top_k).iterrows():
            records.append({
                "task": "Task 2 (Expression)",
                "model": model_key,
                "error_type": "Misclassification (IMPLICIT -> EXPLICIT)",
                "row_id": row["row_id"],
                "comment": row["comment"],
                "gold_label": row["gold_label"],
                "predicted_label": row["predicted_label"],
                "confidence": row["prob_class_0"],
                "gold_evidence": gold_map.get(row["row_id"], ""),
                "analysis": ""
            })

    err_df = pd.DataFrame(records)
    out_path = RESULTS_DIR / "error_cases.csv"
    err_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"PASS: Saved results/error_cases.csv ({len(err_df)} error cases extracted)")
    return err_df


if __name__ == "__main__":
    extract_error_cases("textcnn")
