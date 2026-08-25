"""
Module: Model_final_v3/src/data.py
Description: Data validation, master 80/10/10 stratified split, and token length distribution analysis on Train set.
Uses relative paths exclusively for standalone reproducibility.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from transformers import AutoTokenizer
import pyvi.ViTokenizer as vi_tokenizer

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SPLITS_DIR = BASE_DIR / "data_splits"
RESULTS_DIR = BASE_DIR / "results"


def validate_gold_standard(csv_path: Path = None) -> pd.DataFrame:
    """Validates the gold standard dataset against all expected schema and sanity constraints."""
    if csv_path is None:
        csv_path = DATA_DIR / "gold_standard_final_48670.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Gold standard CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")

    # 1. Row count check
    assert len(df) == 48670, f"Expected 48,670 rows, got {len(df)}"

    # 2. Schema check
    expected_cols = ["row_id", "comment", "toxicity", "expression_type", "evidence"]
    assert list(df.columns) == expected_cols, f"Invalid columns: {list(df.columns)}"

    # 3. Unique row_id check
    assert df["row_id"].nunique() == 48670, "Duplicate row_id values detected!"

    # 4. No null comments
    assert (df["comment"] == "").sum() == 0, "Empty comments detected!"

    # 5. Taxonomy validation
    tox_counts = df["toxicity"].value_counts().to_dict()
    assert tox_counts.get("NON-TOXIC", 0) == 42810, f"Unexpected NON-TOXIC count: {tox_counts.get('NON-TOXIC')}"
    assert tox_counts.get("TOXIC", 0) == 5860, f"Unexpected TOXIC count: {tox_counts.get('TOXIC')}"

    toxic_df = df[df["toxicity"] == "TOXIC"]
    exp_counts = toxic_df["expression_type"].value_counts().to_dict()
    assert exp_counts.get("EXPLICIT", 0) == 4999, f"Unexpected EXPLICIT count: {exp_counts.get('EXPLICIT')}"
    assert exp_counts.get("IMPLICIT", 0) == 861, f"Unexpected IMPLICIT count: {exp_counts.get('IMPLICIT')}"

    # Structural nulls in NON-TOXIC
    non_toxic_df = df[df["toxicity"] == "NON-TOXIC"]
    assert (non_toxic_df["expression_type"] != "").sum() == 0, "NON-TOXIC rows must have empty expression_type!"

    print("PASS: Gold standard validation passed with 100% precision (48,670 rows).")
    return df


def create_master_stratified_split(df: pd.DataFrame = None, output_dir: Path = None, random_state: int = 42):
    """Creates a single master stratified 80/10/10 train/dev/test split on _stratum."""
    if df is None:
        df = validate_gold_standard()
    if output_dir is None:
        output_dir = SPLITS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    # Define composite stratum
    strata = []
    for _, row in df.iterrows():
        if row["toxicity"] == "NON-TOXIC":
            strata.append("NON_TOXIC")
        elif row["expression_type"] == "EXPLICIT":
            strata.append("TOXIC_EXPLICIT")
        elif row["expression_type"] == "IMPLICIT":
            strata.append("TOXIC_IMPLICIT")
        else:
            raise ValueError(f"Unknown stratum for row: {row}")
    df["_stratum"] = strata

    # Step 1: 80% Train vs 20% Temp
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=random_state)
    train_idx, temp_idx = next(sss1.split(df, df["_stratum"]))

    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()

    # Step 2: 50/50 split of Temp into Dev (10%) and Test (10%)
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=random_state)
    dev_rel_idx, test_rel_idx = next(sss2.split(temp_df, temp_df["_stratum"]))

    dev_df = temp_df.iloc[dev_rel_idx].copy()
    test_df = temp_df.iloc[test_rel_idx].copy()

    # Drop helper column
    train_df.drop(columns=["_stratum"], inplace=True)
    dev_df.drop(columns=["_stratum"], inplace=True)
    test_df.drop(columns=["_stratum"], inplace=True)

    # Save to disk
    train_df.to_csv(output_dir / "train.csv", index=False, encoding="utf-8-sig")
    dev_df.to_csv(output_dir / "dev.csv", index=False, encoding="utf-8-sig")
    test_df.to_csv(output_dir / "test.csv", index=False, encoding="utf-8-sig")

    manifest = pd.concat([
        pd.DataFrame({"row_id": train_df["row_id"], "split": "train", "toxicity": train_df["toxicity"], "expression_type": train_df["expression_type"]}),
        pd.DataFrame({"row_id": dev_df["row_id"], "split": "dev", "toxicity": dev_df["toxicity"], "expression_type": dev_df["expression_type"]}),
        pd.DataFrame({"row_id": test_df["row_id"], "split": "test", "toxicity": test_df["toxicity"], "expression_type": test_df["expression_type"]}),
    ], ignore_index=True)
    manifest.to_csv(output_dir / "split_manifest.csv", index=False, encoding="utf-8-sig")

    print(f"PASS: Master split generated -> Train: {len(train_df)}, Dev: {len(dev_df)}, Test: {len(test_df)}")
    return train_df, dev_df, test_df


def compute_token_length_distribution(train_csv_path: Path = None) -> pd.DataFrame:
    """
    Computes real token length distribution for each model tokenizer strictly on the Train set.
    Evaluates both Task 1 (all Train samples) and Task 2 (Train Toxic subset).
    """
    if train_csv_path is None:
        train_csv_path = SPLITS_DIR / "train.csv"

    train_df = pd.read_csv(train_csv_path, dtype="string", keep_default_na=False, encoding="utf-8-sig")

    tasks_data = [
        ("Task 1 (Toxicity)", train_df["comment"].tolist()),
        ("Task 2 (Expression)", train_df[train_df["toxicity"] == "TOXIC"]["comment"].tolist())
    ]

    models_to_evaluate = [
        ("TextCNN (Whitespace)", None, False),
        ("PhoBERT (vinai/phobert-base-v2)", "vinai/phobert-base-v2", True),
        ("ViDeBERTa (Fsoft-AIC/videberta-base)", "Fsoft-AIC/videberta-base", False),
        ("XLM-R (FacebookAI/xlm-roberta-base)", "FacebookAI/xlm-roberta-base", False),
    ]

    records = []

    for task_name, comments in tasks_data:
        n_samples = len(comments)
        for model_label, ckpt, use_pyvi in models_to_evaluate:
            print(f"Analyzing token length: {model_label} on {task_name} ({n_samples} samples)...")
            lengths = []

            if ckpt is None:
                for c in comments:
                    lengths.append(len(str(c).split()))
            else:
                tokenizer = AutoTokenizer.from_pretrained(ckpt)
                for c in comments:
                    text = str(c)
                    if use_pyvi:
                        text = vi_tokenizer.tokenize(text)
                    toks = tokenizer.encode(text, add_special_tokens=True, truncation=False)
                    lengths.append(len(toks))

            lengths = np.array(lengths)
            p50 = float(np.percentile(lengths, 50))
            p90 = float(np.percentile(lengths, 90))
            p95 = float(np.percentile(lengths, 95))
            p99 = float(np.percentile(lengths, 99))

            cov_64 = round(float((lengths <= 64).mean() * 100), 2)
            cov_128 = round(float((lengths <= 128).mean() * 100), 2)
            cov_192 = round(float((lengths <= 192).mean() * 100), 2)
            cov_256 = round(float((lengths <= 256).mean() * 100), 2)
            cov_512 = round(float((lengths <= 512).mean() * 100), 2)

            records.append({
                "model": model_label,
                "task": task_name,
                "n_samples": n_samples,
                "p50": p50,
                "p90": p90,
                "p95": p95,
                "p99": p99,
                "coverage_64": cov_64,
                "coverage_128": cov_128,
                "coverage_192": cov_192,
                "coverage_256": cov_256,
                "coverage_512": cov_512,
                "selected_max_length": 128
            })

    res_df = pd.DataFrame(records)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(RESULTS_DIR / "token_length_analysis.csv", index=False, encoding="utf-8-sig")
    print("PASS: Saved results/token_length_analysis.csv with complete distribution analysis.")
    return res_df


if __name__ == "__main__":
    df = validate_gold_standard()
    create_master_stratified_split(df)
    compute_token_length_distribution()
