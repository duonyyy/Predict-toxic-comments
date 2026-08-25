"""
Module: Model_final_v2/src/plots.py
Description: Generates 8 high-resolution publication-grade figures (DPI >= 300) with clean Vietnamese labels.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
FIGURES_DIR = BASE_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.unicode_minus"] = False


def plot_model_comparison(results_df: pd.DataFrame, task_name="task1", output_name="01_model_comparison_task1.png"):
    """Plots clean bar chart comparing all evaluated models."""
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    models = results_df["Model"].tolist()
    macro_f1 = results_df["Macro_F1"].tolist()
    acc = results_df["Accuracy"].tolist()

    x = np.arange(len(models))
    width = 0.35

    rects1 = ax.bar(x - width/2, macro_f1, width, label="Macro F1-Score", color="#1976D2", edgecolor="black", linewidth=0.8)
    rects2 = ax.bar(x + width/2, acc, width, label="Accuracy", color="#388E3C", edgecolor="black", linewidth=0.8)

    ax.set_ylabel("Điểm số (Score)", fontsize=11, fontweight="bold")
    title_task = "Tác vụ 1 (TOXIC vs NON-TOXIC)" if task_name == "task1" else "Tác vụ 2 (EXPLICIT vs IMPLICIT)"
    ax.set_title(f"So sánh Hiệu năng các Mô hình - {title_task}", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, fontweight="bold")
    ax.set_ylim(0.0, 1.05)
    ax.legend(frameon=True, facecolor="white", edgecolor="gray")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            if not np.isnan(height):
                ax.annotate(f"{height:.4f}",
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, fontweight="bold")

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    out_file = FIGURES_DIR / output_name
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    print(f"PASS: Saved {out_file}")


def plot_confusion_matrix(cm_df: pd.DataFrame, task_name="task1", output_name="03_confusion_matrix_task1_best.png", model_name="TextCNN"):
    """Plots clean annotated heatmap for confusion matrix."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    cmap = "Blues" if task_name == "task1" else "Purples"
    title_task = "Tác vụ 1: TOXIC vs NON-TOXIC" if task_name == "task1" else "Tác vụ 2: EXPLICIT vs IMPLICIT"

    sns.heatmap(cm_df, annot=True, fmt="d", cmap=cmap, cbar=False,
                annot_kws={"size": 13, "weight": "bold"}, ax=ax,
                linewidths=1.2, linecolor="white")

    ax.set_title(f"Ma trận Nhầm lẫn - {model_name}\n({title_task})", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Nhãn Dự đoán (Predicted Label)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Nhãn Thực tế (Actual Label)", fontsize=10, fontweight="bold")

    fig.tight_layout()
    out_file = FIGURES_DIR / output_name
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    print(f"PASS: Saved {out_file}")


def plot_length_analysis(length_df: pd.DataFrame, task_name="task1", output_name="05_length_analysis_task1.png"):
    """Plots performance curve across 5 whitespace token length groups."""
    fig, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
    groups = length_df["length_group"].tolist()
    macro_f1 = length_df["macro_f1"].tolist()
    support = length_df["support"].tolist()

    color_bar = "#B0BEC5"
    color_line = "#D32F2F" if task_name == "task1" else "#7B1FA2"

    ax1.bar(groups, support, color=color_bar, alpha=0.6, width=0.45, label="Số lượng mẫu (Support)", edgecolor="black", linewidth=0.5)
    ax1.set_ylabel("Số lượng mẫu (Support)", fontsize=10, fontweight="bold", color="#37474F")
    ax1.tick_params(axis="y", labelcolor="#37474F")

    ax2 = ax1.twinx()
    ax2.plot(groups, macro_f1, color=color_line, marker="o", linewidth=2.5, markersize=8, label="Macro F1-Score")
    ax2.set_ylabel("Macro F1-Score", fontsize=10, fontweight="bold", color=color_line)
    ax2.tick_params(axis="y", labelcolor=color_line)
    ax2.set_ylim(0.3, 1.0)

    for i, txt in enumerate(macro_f1):
        ax2.annotate(f"{txt:.4f}", (groups[i], macro_f1[i]),
                     textcoords="offset points", xytext=(0, 8), ha="center",
                     fontsize=9, fontweight="bold", color=color_line)

    title_task = "Tác vụ 1: TOXIC vs NON-TOXIC" if task_name == "task1" else "Tác vụ 2: EXPLICIT vs IMPLICIT"
    ax1.set_title(f"Hiệu năng theo Nhóm Độ dài Bình luận - {title_task}", fontsize=12, fontweight="bold", pad=12)
    ax1.set_xlabel("Nhóm Độ dài (Số từ phân tách bằng khoảng trắng)", fontsize=10, fontweight="bold")
    ax1.grid(axis="x", linestyle=":", alpha=0.6)

    fig.tight_layout()
    out_file = FIGURES_DIR / output_name
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    print(f"PASS: Saved {out_file}")


def plot_learning_curve(history_csv_path: Path, task_name="task1", output_name="07_learning_curve_task1_best.png", model_name="TextCNN"):
    """Plots training/dev loss and dev macro-f1 learning curves."""
    df = pd.read_csv(history_csv_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

    epochs = df["epoch"]
    ax1.plot(epochs, df["train_loss"], marker="o", label="Train Loss", color="#E53935", linewidth=2)
    ax1.plot(epochs, df["dev_loss"], marker="s", label="Dev Loss", color="#1E88E5", linewidth=2)
    ax1.set_xlabel("Epoch", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Loss", fontsize=10, fontweight="bold")
    ax1.set_title(f"Đường cong Mất mát (Loss Curve) - {model_name}", fontsize=11, fontweight="bold")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.plot(epochs, df["dev_macro_f1"], marker="^", label="Dev Macro-F1", color="#43A047", linewidth=2.5)
    ax2.plot(epochs, df["dev_accuracy"], marker="d", label="Dev Accuracy", color="#FB8C00", linewidth=1.8, linestyle="--")
    ax2.set_xlabel("Epoch", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Score", fontsize=10, fontweight="bold")
    ax2.set_title(f"Chỉ số Đánh giá trên Dev Set - {model_name}", fontsize=11, fontweight="bold")
    ax2.set_ylim(0.4, 1.0)
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    fig.tight_layout()
    out_file = FIGURES_DIR / output_name
    fig.savefig(out_file, dpi=300)
    plt.close(fig)
    print(f"PASS: Saved {out_file}")
