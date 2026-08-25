"""
Module: Model_final_v2/src/textcnn.py
Description: Full PyTorch 1D-CNN baseline model implementation.
Features fixed, robust checkpoint saving directly to disk on best Dev Macro-F1,
strict Train-only vocabulary building, and standardized Test evaluation.
"""

from collections import Counter
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

BASE_DIR = Path(__file__).resolve().parents[1]
SPLITS_DIR = BASE_DIR / "data_splits"
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "textcnn"
RESULTS_DIR = BASE_DIR / "results"

from metrics import compute_all_metrics


def set_seed(seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class Vocabulary:
    def __init__(self, min_freq=2):
        self.min_freq = min_freq
        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        self.pad_idx = 0
        self.unk_idx = 1
        self.word2idx = {self.pad_token: 0, self.unk_token: 1}
        self.idx2word = {0: self.pad_token, 1: self.unk_token}

    def build_vocab(self, texts):
        counter = Counter()
        for text in texts:
            tokens = str(text).lower().split()
            counter.update(tokens)

        idx = 2
        for word, freq in counter.items():
            if freq >= self.min_freq:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                idx += 1
        return self

    def __len__(self):
        return len(self.word2idx)

    def encode(self, text, max_len=128):
        tokens = str(text).lower().split()
        indices = [self.word2idx.get(w, self.unk_idx) for w in tokens[:max_len]]
        if len(indices) < max_len:
            indices += [self.pad_idx] * (max_len - len(indices))
        return indices


class TextCNNDataset(Dataset):
    def __init__(self, texts, labels, vocab, max_len=128):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        indices = self.vocab.encode(self.texts[idx], max_len=self.max_len)
        return {
            "input_ids": torch.tensor(indices, dtype=torch.long),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long)
        }


class TextCNN(nn.Module):
    def __init__(self, vocab_size, embed_dim=200, num_classes=2, filter_sizes=(2, 3, 4, 5), num_filters=100, dropout=0.5, pad_idx=0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=k)
            for k in filter_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(len(filter_sizes) * num_filters, num_classes)

    def forward(self, input_ids):
        # [batch_size, seq_len] -> [batch_size, seq_len, embed_dim] -> [batch_size, embed_dim, seq_len]
        embedded = self.embedding(input_ids).transpose(1, 2)
        conved = [torch.relu(conv(embedded)) for conv in self.convs]
        pooled = [torch.max_pool1d(c, c.shape[2]).squeeze(2) for c in conved]
        cat = torch.cat(pooled, dim=1)
        dropped = self.dropout(cat)
        logits = self.fc(dropped)
        return logits


def train_textcnn_task(task_name="task1", epochs=8, batch_size=64, lr=1e-3, patience=3):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n=======================================================")
    print(f"STARTING TextCNN TRAINING: {task_name.upper()} on {device}")
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

    class_weights = [w0, w1]
    print(f"Dataset sizes: Train = {len(train_df)}, Dev = {len(dev_df)}, Test = {len(test_df)}")
    print(f"Class weights (computed on Train): {class_weights}")

    # Build Vocabulary strictly on Train
    vocab = Vocabulary(min_freq=2).build_vocab(train_df["comment"].tolist())
    print(f"Train Vocabulary size: {len(vocab)}")

    train_ds = TextCNNDataset(train_df["comment"].tolist(), [label_map[l] for l in train_df[label_col]], vocab, max_len=128)
    dev_ds = TextCNNDataset(dev_df["comment"].tolist(), [label_map[l] for l in dev_df[label_col]], vocab, max_len=128)
    test_ds = TextCNNDataset(test_df["comment"].tolist(), [label_map[l] for l in test_df[label_col]], vocab, max_len=128)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    dev_loader = DataLoader(dev_ds, batch_size=batch_size * 2, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size * 2, shuffle=False)

    model = TextCNN(vocab_size=len(vocab), embed_dim=200, num_classes=2, filter_sizes=(2, 3, 4, 5), num_filters=100, dropout=0.5, pad_idx=0).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float).to(device))

    task_artifact_dir = ARTIFACTS_DIR / task_name
    task_artifact_dir.mkdir(parents=True, exist_ok=True)
    best_checkpoint_path = task_artifact_dir / "best_model.pt"

    best_dev_macro_f1 = -1.0
    best_dev_metrics = None
    best_epoch = -1
    patience_counter = 0
    history = []

    start_train_time = time.time()
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            logits = model(input_ids)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(labels)
        train_loss /= len(train_ds)

        # Validation
        model.eval()
        dev_loss = 0.0
        dev_preds, dev_targets = [], []
        with torch.no_grad():
            for batch in dev_loader:
                input_ids = batch["input_ids"].to(device)
                labels = batch["labels"].to(device)
                logits = model(input_ids)
                loss = criterion(logits, labels)

                dev_loss += loss.item() * len(labels)
                preds = torch.argmax(logits, dim=1).cpu().numpy()
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
            "dev_macro_f1": dev_macro_f1
        }
        history.append(log_item)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Dev Loss: {dev_loss:.4f} | Dev Acc: {dev_m['Accuracy']:.4f} | Dev Macro-F1: {dev_macro_f1:.4f}")

        if dev_macro_f1 > best_dev_macro_f1:
            best_dev_macro_f1 = dev_macro_f1
            best_epoch = epoch
            best_dev_metrics = dev_m
            patience_counter = 0
            # CRITICAL FIX: Save best model checkpoint directly to disk
            torch.save(model.state_dict(), best_checkpoint_path)
            print(f"  -> Best Dev Macro-F1: {best_dev_macro_f1:.4f}. Saved checkpoint to disk: {best_checkpoint_path}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered at epoch {epoch}.")
                break

    train_time_sec = round(time.time() - start_train_time, 2)
    pd.DataFrame(history).to_csv(task_artifact_dir / "learning_history.csv", index=False)

    # CRITICAL FIX: Load best checkpoint directly from disk for Test evaluation
    print(f"\nRestoring best checkpoint from disk (Epoch {best_epoch}, Dev Macro-F1: {best_dev_macro_f1:.4f}) for Test evaluation...")
    model.load_state_dict(torch.load(best_checkpoint_path, map_location=device))
    model.eval()

    test_preds, test_probs, test_targets = [], [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            logits = model(input_ids)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            test_probs.extend(probs)
            test_preds.extend(preds)
            test_targets.extend(labels.cpu().numpy())

    test_eval_res = compute_all_metrics(test_targets, test_preds, target_names)
    test_metrics = test_eval_res["summary"]
    per_class_df = test_eval_res["per_class_df"]
    cm_df = test_eval_res["confusion_matrix_df"]

    # Save Predictions
    inv_label_map = {v: k for k, v in label_map.items()}
    pred_df = test_df[["row_id", "comment", label_col]].copy()
    pred_df.rename(columns={label_col: "gold_label"}, inplace=True)
    pred_df["predicted_label"] = [inv_label_map[p] for p in test_preds]
    pred_df["prob_class_0"] = [round(p[0], 4) for p in test_probs]
    pred_df["prob_class_1"] = [round(p[1], 4) for p in test_probs]
    pred_df["correct"] = pred_df["gold_label"] == pred_df["predicted_label"]

    preds_dir = RESULTS_DIR / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(preds_dir / f"textcnn_{task_name}.csv", index=False, encoding="utf-8-sig")

    cm_dir = RESULTS_DIR / "confusion_matrices"
    cm_dir.mkdir(parents=True, exist_ok=True)
    cm_df.to_csv(cm_dir / f"textcnn_{task_name}_cm.csv", encoding="utf-8-sig")

    print(f"\n--- TEST RESULTS [TextCNN - {task_name.upper()}] ---")
    print(json.dumps(test_metrics, indent=2))
    print("\nPer-class Metrics:\n", per_class_df)
    print("\nConfusion Matrix:\n", cm_df)

    return {
        "model": "TextCNN (Baseline)",
        "task": task_name,
        "best_epoch": best_epoch,
        "train_time_sec": train_time_sec,
        "dev_metrics": best_dev_metrics,
        "test_metrics": test_metrics,
        "per_class_df": per_class_df,
        "confusion_matrix_df": cm_df,
        "checkpoint_path": str(best_checkpoint_path.relative_to(BASE_DIR))
    }


if __name__ == "__main__":
    train_textcnn_task("task1")
    train_textcnn_task("task2")
