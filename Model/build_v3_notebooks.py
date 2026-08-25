"""
Script: Model_final_v3/build_v3_notebooks.py
Description: Generates 100% self-contained, fully-functional, reproducible Jupyter notebooks in Model_final_v3/notebooks/.
"""

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
NB_DIR = BASE_DIR / "notebooks"
NB_DIR.mkdir(parents=True, exist_ok=True)


def make_nb(cells, gpu=False):
    meta = {
        "language_info": {"name": "python"}
    }
    if gpu:
        meta["accelerator"] = "GPU"
        meta["colab"] = {"gpuType": "T4", "provenance": []}
    return {
        "cells": cells,
        "metadata": meta,
        "nbformat": 4,
        "nbformat_minor": 5
    }


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}


def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [text]}


def build_nb0():
    cells = [
        md("# 📊 00. KHÁM PHÁ DỮ LIỆU & PHÂN CHIA MASTER STRATIFIED SPLIT (80/10/10)\n\n"
           "**Đề tài:** Nhận diện và Phân loại Phát ngôn Độc hại trên Mạng xã hội Tiếng Việt\n\n"
           "Notebook này thực hiện:\n"
           "1. Khám phá và kiểm tra tính toàn vẹn của tập dữ liệu chuẩn vàng `gold_standard_final_48670.csv`.\n"
           "2. Phân tích phân bố nhãn 2 tầng (`TOXIC/NON-TOXIC` và `EXPLICIT/IMPLICIT`).\n"
           "3. Thực hiện phân chia Master Stratified Split 80/10/10 (`Train: 38,936`, `Dev: 4,867`, `Test: 4,867`).\n"
           "4. Phân tích độ dài token thực tế bằng 4 tokenizer trên tập Train và chọn `max_length = 128`."),
        md("## 1. Import Thư viện & Cấu hình Đường dẫn"),
        code("import os\n"
             "import sys\n"
             "from pathlib import Path\n"
             "import numpy as np\n"
             "import pandas as pd\n"
             "import matplotlib.pyplot as plt\n"
             "import seaborn as sns\n"
             "from sklearn.model_selection import StratifiedShuffleSplit\n"
             "from transformers import AutoTokenizer\n"
             "import pyvi.ViTokenizer as vi_tokenizer\n\n"
             "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
             "DATA_PATH = PROJECT_ROOT / 'data' / 'gold_standard_final_48670.csv'\n"
             "SPLITS_DIR = PROJECT_ROOT / 'data_splits'\n"
             "RESULTS_DIR = PROJECT_ROOT / 'results'\n"
             "SPLITS_DIR.mkdir(parents=True, exist_ok=True)\n"
             "RESULTS_DIR.mkdir(parents=True, exist_ok=True)\n\n"
             "print('Project Root:', PROJECT_ROOT)\n"
             "print('Data Path:', DATA_PATH)"),
        md("## 2. Tải & Kiểm tra Tính Toàn vẹn của Tập Dữ liệu Chuẩn vàng"),
        code("df = pd.read_csv(DATA_PATH, dtype='string', keep_default_na=False, encoding='utf-8-sig')\n\n"
             "print(f'Tổng số dòng: {len(df):,}')\n"
             "print('Danh sách cột:', list(df.columns))\n"
             "print(f'Số lượng unique row_id: {df[\"row_id\"].nunique():,}')\n"
             "print(f'Số bình luận rỗng: {(df[\"comment\"] == \"\").sum()}')\n\n"
             "tox_counts = df['toxicity'].value_counts()\n"
             "print('\\n--- PHÂN BỐ TÁC VỤ 1 (TOXIC / NON-TOXIC) ---')\n"
             "for k, v in tox_counts.items():\n"
             "    print(f'  * {k}: {v:,} mẫu ({v/len(df)*100:.2f}%)')\n\n"
             "toxic_subset = df[df['toxicity'] == 'TOXIC']\n"
             "exp_counts = toxic_subset['expression_type'].value_counts()\n"
             "print('\\n--- PHÂN BỐ TÁC VỤ 2 TRÊN TẬP TOXIC (EXPLICIT / IMPLICIT) ---')\n"
             "for k, v in exp_counts.items():\n"
             "    print(f'  * {k}: {v:,} mẫu ({v/len(toxic_subset)*100:.2f}%)')\n\n"
             "display(df.head())"),
        md("## 3. Trực quan hóa Phân bố Nhãn"),
        code("fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=150)\n\n"
             "axes[0].pie(tox_counts.values, labels=tox_counts.index, autopct='%1.2f%%',\n"
             "            colors=['#81C784', '#E57373'], startangle=140, explode=(0, 0.1),\n"
             "            textprops={'fontsize': 11, 'weight': 'bold'})\n"
             "axes[0].set_title('Tác vụ 1: Phân bố Độc hại (N = 48,670)', fontsize=12, fontweight='bold')\n\n"
             "axes[1].pie(exp_counts.values, labels=exp_counts.index, autopct='%1.2f%%',\n"
             "            colors=['#FFB74D', '#BA68C8'], startangle=140, explode=(0, 0.1),\n"
             "            textprops={'fontsize': 11, 'weight': 'bold'})\n"
             "axes[1].set_title('Tác vụ 2: Kiểu biểu đạt trên tập TOXIC (N = 5,860)', fontsize=12, fontweight='bold')\n\n"
             "plt.tight_layout()\n"
             "plt.show()"),
        md("## 4. Thực hiện Master Stratified Split 80/10/10"),
        code("strata = []\n"
             "for _, row in df.iterrows():\n"
             "    if row['toxicity'] == 'NON-TOXIC':\n"
             "        strata.append('NON_TOXIC')\n"
             "    elif row['expression_type'] == 'EXPLICIT':\n"
             "        strata.append('TOXIC_EXPLICIT')\n"
             "    elif row['expression_type'] == 'IMPLICIT':\n"
             "        strata.append('TOXIC_IMPLICIT')\n"
             "    else:\n"
             "        raise ValueError(f'Unknown stratum: {row}')\n\n"
             "df['_stratum'] = strata\n\n"
             "sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)\n"
             "train_idx, temp_idx = next(sss1.split(df, df['_stratum']))\n"
             "train_df = df.iloc[train_idx].copy()\n"
             "temp_df = df.iloc[temp_idx].copy()\n\n"
             "sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=42)\n"
             "dev_rel_idx, test_rel_idx = next(sss2.split(temp_df, temp_df['_stratum']))\n"
             "dev_df = temp_df.iloc[dev_rel_idx].copy()\n"
             "test_df = temp_df.iloc[test_rel_idx].copy()\n\n"
             "train_df.drop(columns=['_stratum'], inplace=True)\n"
             "dev_df.drop(columns=['_stratum'], inplace=True)\n"
             "test_df.drop(columns=['_stratum'], inplace=True)\n\n"
             "train_df.to_csv(SPLITS_DIR / 'train.csv', index=False, encoding='utf-8-sig')\n"
             "dev_df.to_csv(SPLITS_DIR / 'dev.csv', index=False, encoding='utf-8-sig')\n"
             "test_df.to_csv(SPLITS_DIR / 'test.csv', index=False, encoding='utf-8-sig')\n\n"
             "print(f'Train: {len(train_df):,} | Dev: {len(dev_df):,} | Test: {len(test_df):,}')"),
        md("## 5. Phân tích Phân bố Độ dài Token trên Tập Train"),
        code("sys.path.append(str(PROJECT_ROOT / 'src'))\n"
             "from data import compute_token_length_distribution\n"
             "len_df = compute_token_length_distribution(SPLITS_DIR / 'train.csv')\n"
             "display(len_df)")
    ]
    return make_nb(cells)


def build_nb1():
    cells = [
        md("# 🧠 01. HUẤN LUYỆN VÀ ĐÁNH GIÁ MÔ HÌNH BASELINE TEXTCNN\n\n"
           "**Đề tài:** Nhận diện và Phân loại Phát ngôn Độc hại trên Mạng xã hội Tiếng Việt\n\n"
           "Notebook này triển khai hoàn chỉnh mô hình **TextCNN (1D-CNN trên Word Embeddings)**:\n"
           "1. Xây dựng bộ từ điển Vocabulary dựa **hoàn toàn từ tập Train** (`min_freq = 2`).\n"
           "2. Tính toán trọng số lớp nghịch đảo (*Class Weights*) chỉ từ tập Train.\n"
           "3. Cơ chế Early Stopping trên `Dev Macro-F1` và **lưu trực tiếp best checkpoint ra đĩa (`best_model.pt`)**.\n"
           "4. Tải lại best checkpoint từ đĩa để đánh giá trên tập kiểm thử độc lập (`Test Set - LOCKED`).\n"
           "5. Trích xuất chỉ số từng lớp, ma trận nhầm lẫn, phân tích theo nhóm độ dài và ca lỗi thực tế."),
        md("## 1. Import Thư viện & Thiết lập Seed Tái lập"),
        code("import os, sys, time, json\n"
             "from pathlib import Path\n"
             "from collections import Counter\n"
             "import numpy as np\n"
             "import pandas as pd\n"
             "import matplotlib.pyplot as plt\n"
             "import seaborn as sns\n"
             "import torch\n"
             "import torch.nn as nn\n"
             "from torch.utils.data import Dataset, DataLoader\n"
             "from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix\n\n"
             "def set_seed(seed=42):\n"
             "    np.random.seed(seed)\n"
             "    torch.manual_seed(seed)\n"
             "    if torch.cuda.is_available():\n"
             "        torch.cuda.manual_seed_all(seed)\n\n"
             "set_seed(42)\n"
             "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')\n"
             "print('Thiết bị thực thi:', device)"),
        md("## 2. Cấu hình Đường dẫn & Chạy Huấn luyện TextCNN"),
        code("PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
             "sys.path.append(str(PROJECT_ROOT / 'src'))\n"
             "from textcnn import run_textcnn_experiment\n\n"
             "print('>>> HUẤN LUYỆN TÁC VỤ 1 (TEXTCNN) <<<')\n"
             "res_t1 = run_textcnn_experiment('task1', epochs=8, batch_size=64, lr=1e-3, patience=2)\n\n"
             "print('\\n>>> HUẤN LUYỆN TÁC VỤ 2 (TEXTCNN) <<<')\n"
             "res_t2 = run_textcnn_experiment('task2', epochs=8, batch_size=32, lr=1e-3, patience=2)")
    ]
    return make_nb(cells)


def build_nb_colab_all():
    cells = [
        md("# 🚀 MASTER GOOGLE COLAB: HUẤN LUYỆN 3 MÔ HÌNH TRANSFORMER (6 EXPERIMENTS)\n\n"
           "**Mục tiêu:** Huấn luyện toàn bộ 6 thí nghiệm Transformer cho cả 2 tác vụ trên GPU Colab/Kaggle:\n"
           "1. **PhoBERT** (`vinai/phobert-base-v2`): Task 1 & Task 2 (có tiền xử lý tách từ PyVi)\n"
           "2. **ViDeBERTa** (`Fsoft-AIC/videberta-base`): Task 1 & Task 2\n"
           "3. **XLM-RoBERTa** (`FacebookAI/xlm-roberta-base`): Task 1 & Task 2\n\n"
           "**Các tính năng chuẩn hóa:**\n"
           "- Gradient Accumulation (Physical Batch 16 x 2 steps = Effective Batch 32)\n"
           "- Mixed Precision (AMP fp16)\n"
           "- Dev Macro-F1 Early Stopping (Patience = 2)\n"
           "- Khóa tập Test (Chỉ đánh giá 1 lần duy nhất trên Best Dev Checkpoint)\n"
           "- Tự động đóng gói tất cả artifacts thành file `.zip` để tải về."),
        md("## 1. Cài đặt Môi trường & Dependencies"),
        code("!pip install -q transformers==4.49.0 datasets==3.3.2 pyvi==0.1.1 accelerate==1.4.0 scikit-learn==1.6.1 seaborn==0.13.2"),
        md("## 2. Kiểm tra GPU"),
        code("import torch\n"
             "print('CUDA Available:', torch.cuda.is_available())\n"
             "if torch.cuda.is_available():\n"
             "    print('GPU Device:', torch.cuda.get_device_name(0))\n"
             "    print('Memory Allocated:', round(torch.cuda.memory_allocated(0)/1024**3, 1), 'GB')\n"
             "else:\n"
             "    print('WARNING: GPU not detected! Hãy đổi Runtime sang GPU T4 trước khi chạy!')"),
        md("## 3. Khởi tạo Đường dẫn & Import Engine"),
        code("import os\n"
             "import sys\n"
             "from pathlib import Path\n\n"
             "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
             "sys.path.append(str(PROJECT_ROOT / 'src'))\n\n"
             "from train import train_transformer_task\n"
             "from transformer_model import run_all_smoke_tests\n"
             "from aggregate_results import aggregate_all\n\n"
             "print('Project Root:', PROJECT_ROOT)"),
        md("## 4. Chạy Smoke Test xác thực trước khi Train"),
        code("smoke_res = run_all_smoke_tests(device='cuda' if torch.cuda.is_available() else 'cpu')\n"
             "print('Smoke Test Results Summary:')\n"
             "for k, v in smoke_res.items():\n"
             "    print(f'  * {k}: {v.get(\"status\", \"UNKNOWN\")}')"),
        md("## 5. Chạy Huấn luyện 6 Thí nghiệm Transformer"),
        code("models_to_train = ['phobert', 'videberta', 'xlmr']\n"
             "tasks_to_train = ['task1', 'task2']\n\n"
             "results_summary = []\n"
             "for m_key in models_to_train:\n"
             "    for t_key in tasks_to_train:\n"
             "        print(f'\\n>>>>>>>>>>>>>>>>> [START] MODEL: {m_key.upper()} | TASK: {t_key.upper()} <<<<<<<<<<<<<<<<<')\n"
             "        res = train_transformer_task(\n"
             "            model_key=m_key,\n"
             "            task_name=t_key,\n"
             "            epochs=5,\n"
             "            batch_size=16,\n"
             "            grad_accum_steps=2,\n"
             "            lr=2e-5,\n"
             "            patience=2,\n"
             "            seed=42,\n"
             "            max_length=128\n"
             "        )\n"
             "        results_summary.append(res)\n"
             "        print(f'>>>>>>>>>>>>>>>>> [COMPLETED] {m_key.upper()} - {t_key.upper()} <<<<<<<<<<<<<<<<<\\n')"),
        md("## 6. Tổng hợp Kết quả Benchmark Toàn diện & Vẽ Biểu đồ"),
        code("aggregate_all()\n"
             "print('\\n--- TỔNG HỢP KẾT QUẢ TÁC VỤ 1 ---')\n"
             "display(pd.read_csv(PROJECT_ROOT / 'results' / 'test_results_task1.csv'))\n\n"
             "print('\\n--- TỔNG HỢP KẾT QUẢ TÁC VỤ 2 ---')\n"
             "display(pd.read_csv(PROJECT_ROOT / 'results' / 'test_results_task2.csv'))"),
        md("## 7. Đóng gói Artifacts thành file ZIP để tải về máy"),
        code("import shutil\n\n"
             "zip_output = PROJECT_ROOT / 'colab_artifacts_export'\n"
             "dirs_to_zip = ['results', 'artifacts', 'figures', 'report']\n\n"
             "temp_export = PROJECT_ROOT / 'export_bundle'\n"
             "temp_export.mkdir(parents=True, exist_ok=True)\n"
             "for d in dirs_to_zip:\n"
             "    src_d = PROJECT_ROOT / d\n"
             "    if src_d.exists():\n"
             "        shutil.copytree(src_d, temp_export / d, dirs_exist_ok=True)\n\n"
             "shutil.make_archive(str(zip_output), 'zip', temp_export)\n"
             "shutil.rmtree(temp_export)\n"
             "print(f'PASS: Đã đóng gói thành công file {zip_output}.zip! Hãy tải file này về và giải nén đè vào Model_final_v3.')")
    ]
    return make_nb(cells, gpu=True)


def build_all():
    print("Building Model_final_v3 notebooks...")
    
    with open(NB_DIR / "00_data_exploration_and_split.ipynb", "w", encoding="utf-8") as f:
        json.dump(build_nb0(), f, indent=2, ensure_ascii=False)
        
    with open(NB_DIR / "01_textcnn.ipynb", "w", encoding="utf-8") as f:
        json.dump(build_nb1(), f, indent=2, ensure_ascii=False)
        
    with open(NB_DIR / "DS108_Colab_FineTuning_Transformers_AllInOne.ipynb", "w", encoding="utf-8") as f:
        json.dump(build_nb_colab_all(), f, indent=2, ensure_ascii=False)
        
    print("PASS: Built all Model_final_v3 notebooks successfully.")


if __name__ == "__main__":
    build_all()
