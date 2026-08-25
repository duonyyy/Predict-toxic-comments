"""
Module: Model_final_v3/src/train.py
Description: Universal training and fine-tuning engine for TextCNN and Transformer models (PhoBERT, ViDeBERTa, XLM-R).
Includes Gradient Accumulation, Mixed Precision (AMP), Dev Macro-F1 Early Stopping (patience=2),
and exhaustive artifact export (best_model, tokenizer, history, metrics, predictions, confusion matrix).
"""

from pathlib import Path
import argparse
import json
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
import pyvi.ViTokenizer as vi_tokenizer

BASE_DIR = Path(__file__).resolve().parents[1]
SPLITS_DIR = BASE_DIR / "data_splits"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
RESULTS_DIR = BASE_DIR / "results"

from metrics import compute_all_metrics
from transformer_model import TRANSFORMER_MODELS


def set_seed(seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class TransformerDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=128, use_pyvi=False):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.use_pyvi = use_pyvi

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        if self.use_pyvi:
            text = vi_tokenizer.tokenize(text)

        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long)
        }


def train_transformer_task(
    model_key: str,
    task_name="task1",
    epochs=5,
    batch_size=16,
    grad_accum_steps=2,
    lr=2e-5,
    patience=2,
    seed=42,
    max_length=128
):
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = TRANSFORMER_MODELS[model_key]
    effective_batch_size = batch_size * grad_accum_steps

    print(f"\n=======================================================")
    print(f"STARTING {cfg['name']} TRAINING: {task_name.upper()}")
    print(f"Device: {device} | Physical Batch: {batch_size} | Grad Accum: {grad_accum_steps} | Effective Batch: {effective_batch_size}")
    print(f"=======================================================")

    # 1. Load Data
    train_df = pd.read_csv(SPLITS_DIR / "train.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    dev_df = pd.read_csv(SPLITS_DIR / "dev.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")
    test_df = pd.read_csv(SPLITS_DIR / "test.csv", dtype="string", keep_default_na=False, encoding="utf-8-sig")

    if task_name == "task1":
        label_col = "toxicity"
        label_map = {"NON-TOXIC": 0, "TOXIC": 1}
        target_names = ["NON-TOXIC", "TOXIC"]
        w0 = len(train_df) / (2.0 * (train_df["toxicity"] == "NON-TOXIC").sum())
        w1 = len(train_df) / (2.0 * (train_df["toxicity"] == "TOXIC").sum())
    else:
        train_df = train_df[train_df["toxicity"] == "TOXIC"].reset_index(drop=True)
        dev_df = dev_df[dev_df["toxicity"] == "TOXIC"].reset_index(drop=True)
        test_df = test_df[test_df["toxicity"] == "TOXIC"].reset_index(drop=True)
        label_col = "expression_type"
        label_map = {"EXPLICIT": 0, "IMPLICIT": 1}
        target_names = ["EXPLICIT", "IMPLICIT"]
        w0 = len(train_df) / (2.0 * (train_df["expression_type"] == "EXPLICIT").sum())
        w1 = len(train_df) / (2.0 * (train_df["expression_type"] == "IMPLICIT").sum())

    class_weights = [round(float(w0), 6), round(float(w1), 6)]
    print(f"Dataset sizes: Train = {len(train_df)}, Dev = {len(dev_df)}, Test = {len(test_df)}")
    print(f"Class Weights (from Train only): {target_names[0]} = {class_weights[0]}, {target_names[1]} = {class_weights[1]}")

    tokenizer = AutoTokenizer.from_pretrained(cfg["ckpt"])
    model = AutoModelForSequenceClassification.from_pretrained(cfg["ckpt"], num_labels=2).to(device)

    train_ds = TransformerDataset(train_df["comment"].tolist(), [label_map[l] for l in train_df[label_col]], tokenizer, max_len=max_length, use_pyvi=cfg["use_pyvi"])
    dev_ds = TransformerDataset(dev_df["comment"].tolist(), [label_map[l] for l in dev_df[label_col]], tokenizer, max_len=max_length, use_pyvi=cfg["use_pyvi"])
    test_ds = TransformerDataset(test_df["comment"].tolist(), [label_map[l] for l in test_df[label_col]], tokenizer, max_len=max_length, use_pyvi=cfg["use_pyvi"])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, pin_memory=torch.cuda.is_available())
    dev_loader = DataLoader(dev_ds, batch_size=batch_size * 2, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size * 2, shuffle=False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_training_steps = (len(train_loader) // grad_accum_steps) * epochs
    warmup_steps = int(total_training_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_training_steps)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float).to(device))
    scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

    save_dir = ARTIFACTS_DIR / model_key / task_name
    save_dir.mkdir(parents=True, exist_ok=True)
    best_model_dir = save_dir / "best_model"
    best_model_dir.mkdir(parents=True, exist_ok=True)
    tokenizer_dir = save_dir / "tokenizer"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)

    best_dev_macro_f1 = -1.0
    best_dev_metrics = None
    best_epoch = -1
    patience_counter = 0
    history = []

    start_train_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = criterion(outputs.logits, labels)
                loss = loss / grad_accum_steps

            scaler.scale(loss).backward()
            train_loss += loss.item() * grad_accum_steps * len(labels)

            if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()

        train_loss /= len(train_ds)

        # Validation phase
        model.eval()
        dev_loss = 0.0
        dev_preds, dev_targets = [], []
        with torch.no_grad():
            for batch in dev_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)

                with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                    loss = criterion(outputs.logits, labels)

                dev_loss += loss.item() * len(labels)
                preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                dev_preds.extend(preds)
                dev_targets.extend(labels.cpu().numpy())
        dev_loss /= len(dev_ds)

        eval_res = compute_all_metrics(dev_targets, dev_preds, target_names)
        dev_m = eval_res["summary"]
        dev_macro_f1 = dev_m["Macro_F1"]

        log_item = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "dev_loss": round(dev_loss, 4),
            "dev_accuracy": dev_m["Accuracy"],
            "dev_macro_precision": dev_m["Macro_Precision"],
            "dev_macro_recall": dev_m["Macro_Recall"],
            "dev_macro_f1": dev_macro_f1
        }
        history.append(log_item)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Dev Loss: {dev_loss:.4f} | Dev Acc: {dev_m['Accuracy']:.4f} | Dev Macro-F1: {dev_macro_f1:.4f}")

        # Checkpoint selection on Dev Macro-F1
        if dev_macro_f1 > best_dev_macro_f1:
            best_dev_macro_f1 = dev_macro_f1
            best_epoch = epoch
            best_dev_metrics = dev_m
            patience_counter = 0

            # Save best checkpoint to disk
            model.save_pretrained(best_model_dir)
            tokenizer.save_pretrained(tokenizer_dir)
            print(f"  -> [NEW BEST] Dev Macro-F1: {best_dev_macro_f1:.4f}. Saved checkpoint to {best_model_dir}")
        else:
            patience_counter += 1
            print(f"  -> No improvement. Early stopping patience: {patience_counter}/{patience}")
            if patience_counter >= patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                break

    train_time_sec = round(time.time() - start_train_time, 2)
    history_df = pd.DataFrame(history)
    history_df.to_csv(save_dir / "training_history.csv", index=False)

    # Restore Best Checkpoint for Single Test Evaluation
    print(f"\nRestoring best checkpoint from disk (Epoch {best_epoch}, Dev Macro-F1: {best_dev_macro_f1:.4f}) for Test evaluation...")
    model = AutoModelForSequenceClassification.from_pretrained(best_model_dir).to(device)
    model.eval()

    test_preds, test_probs, test_targets = [], [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1).cpu().numpy()

            preds = np.argmax(probs, axis=1)
            test_probs.extend(probs)
            test_preds.extend(preds)
            test_targets.extend(labels.cpu().numpy())

    test_eval_res = compute_all_metrics(test_targets, test_preds, target_names)
    test_metrics = test_eval_res["summary"]
    per_class_df = test_eval_res["per_class_df"]
    cm_df = test_eval_res["confusion_matrix_df"]

    # 1. Save artifact files inside artifacts/{model}/{task}/
    per_class_df.to_csv(save_dir / "classification_report.csv", index=False, encoding="utf-8-sig")
    cm_df.to_csv(save_dir / "confusion_matrix.csv", encoding="utf-8-sig")
    with open(save_dir / "dev_metrics.json", "w", encoding="utf-8") as f:
        json.dump(best_dev_metrics, f, indent=2)
    with open(save_dir / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(test_metrics, f, indent=2)

    exp_config = {
        "model_key": model_key,
        "model_name": cfg["name"],
        "checkpoint": cfg["ckpt"],
        "task_name": task_name,
        "label_mapping": label_map,
        "class_weights": class_weights,
        "max_length": max_length,
        "physical_batch_size": batch_size,
        "gradient_accumulation_steps": grad_accum_steps,
        "effective_batch_size": effective_batch_size,
        "learning_rate": lr,
        "weight_decay": 0.01,
        "warmup_ratio": 0.1,
        "early_stopping_patience": patience,
        "seed": seed,
        "best_epoch": best_epoch,
        "training_time_seconds": train_time_sec,
        "device": str(device),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"
    }
    with open(save_dir / "experiment_config.json", "w", encoding="utf-8") as f:
        json.dump(exp_config, f, indent=2)

    # 2. Save Predictions to results/predictions/{model_key}_{task_name}.csv
    inv_label_map = {v: k for k, v in label_map.items()}
    pred_df = test_df[["row_id", "comment", label_col]].copy()
    pred_df.rename(columns={label_col: "gold_label"}, inplace=True)
    pred_df["predicted_label"] = [inv_label_map[p] for p in test_preds]
    pred_df["prob_class_0"] = [round(float(p[0]), 6) for p in test_probs]
    pred_df["prob_class_1"] = [round(float(p[1]), 6) for p in test_probs]
    pred_df["correct"] = pred_df["gold_label"] == pred_df["predicted_label"]

    preds_dir = RESULTS_DIR / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)
    pred_file = preds_dir / f"{model_key}_{task_name}.csv"
    pred_df.to_csv(pred_file, index=False, encoding="utf-8-sig")

    # 3. Save Confusion Matrix to results/confusion_matrices/{model_key}_{task_name}_cm.csv
    cm_dir = RESULTS_DIR / "confusion_matrices"
    cm_dir.mkdir(parents=True, exist_ok=True)
    cm_df.to_csv(cm_dir / f"{model_key}_{task_name}_cm.csv", encoding="utf-8-sig")

    print(f"\n--- TEST RESULTS [{cfg['name']} - {task_name.upper()}] ---")
    print(f"Accuracy:        {test_metrics['Accuracy']:.4f}")
    print(f"Macro Precision: {test_metrics['Macro_Precision']:.4f}")
    print(f"Macro Recall:    {test_metrics['Macro_Recall']:.4f}")
    print(f"Macro F1:        {test_metrics['Macro_F1']:.4f}")
    print(f"Weighted F1:     {test_metrics['Weighted_F1']:.4f}")
    print(f"Saved artifacts to {save_dir} and predictions to {pred_file}")

    return {
        "model": cfg["name"],
        "task": task_name,
        "best_epoch": best_epoch,
        "train_time_sec": train_time_sec,
        "dev_metrics": best_dev_metrics,
        "test_metrics": test_metrics,
        "per_class_df": per_class_df,
        "confusion_matrix_df": cm_df
    }


def main():
    parser = argparse.ArgumentParser(description="Model_final_v3 Training Engine")
    parser.add_argument("--model", type=str, required=True, choices=["textcnn", "phobert", "videberta", "xlmr"], help="Model architecture")
    parser.add_argument("--task", type=str, required=True, choices=["task1", "task2"], help="Task name (task1 or task2)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of max epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Physical batch size per step")
    parser.add_argument("--grad_accum", type=int, default=2, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--patience", type=int, default=2, help="Early stopping patience")
    parser.add_argument("--max_length", type=int, default=128, help="Max sequence token length")
    args = parser.parse_args()

    if args.model == "textcnn":
        from textcnn import run_textcnn_experiment
        run_textcnn_experiment(task_name=args.task, epochs=args.epochs, batch_size=args.batch_size * args.grad_accum, lr=args.lr, patience=args.patience)
    else:
        train_transformer_task(
            model_key=args.model,
            task_name=args.task,
            epochs=args.epochs,
            batch_size=args.batch_size,
            grad_accum_steps=args.grad_accum,
            lr=args.lr,
            patience=args.patience,
            max_length=args.max_length
        )


if __name__ == "__main__":
    main()
