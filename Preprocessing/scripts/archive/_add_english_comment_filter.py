import json
from pathlib import Path

import nbformat


path = Path(r'C:\Users\Admin\Desktop\DS108\Preprocessing\clearing_data.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))

for cell in nb['cells']:
    source = ''.join(cell.get('source', []))

    if cell['cell_type'] == 'code' and source.startswith('# Cài package vào đúng Python kernel hiện tại'):
        cell['source'] = [source.replace(
            '%pip install pandas regex',
            '%pip install pandas regex lingua-language-detector',
        )]

    if cell['cell_type'] == 'code' and source.startswith('from pathlib import Path'):
        source = source.replace(
            'import pandas as pd\n',
            'import pandas as pd\nfrom lingua import Language, LanguageDetectorBuilder\n',
        )
        source = source.replace(
            'from IPython.display import display\n',
            'from IPython.display import display\n\n'
            'LANGUAGE_DETECTOR = LanguageDetectorBuilder.from_languages(\n'
            '    Language.VIETNAMESE,\n'
            '    Language.ENGLISH,\n'
            ').build()\n',
        )
        cell['source'] = [source]

    if cell['cell_type'] == 'markdown' and '### 5.3.' in source:
        cell['source'] = [
            '''### 5.3. Loại bỏ quảng cáo và nội dung không hữu ích

Các bình luận được loại khi thuộc một trong các trường hợp: quảng cáo rõ ràng,
nội dung hệ thống, chuỗi ký tự vô nghĩa, dưới 2 từ, trên 200 từ hoặc được nhận
diện là tiếng Anh với độ tin cậy cao.

Số từ được tính bằng các cụm ký tự tách bởi khoảng trắng; emoji đơn lẻ như `😂`
hoặc `✅` được tính là 1 từ và bị loại. Nhận diện ngôn ngữ chỉ so sánh tiếng Việt
và tiếng Anh, yêu cầu độ tin cậy từ 0,95 để hạn chế xóa nhầm comment trộn ngôn ngữ.
'''
        ]

    if cell['cell_type'] == 'code' and source.startswith('# 5.3. Hàm nhận biết comment cần loại bỏ'):
        source = source.replace(
            "def join_removal_reasons(row):\n",
            '''def is_confident_english_comment(text, minimum_confidence=0.95):
    """Chỉ nhận diện tiếng Anh khi xác suất cao hơn ngưỡng đã chọn."""
    text = str(text).strip()
    if not re.search(r'[A-Za-z]', text):
        return False

    scores = {
        item.language: item.value
        for item in LANGUAGE_DETECTOR.compute_language_confidence_values(text)
    }
    english_score = scores.get(Language.ENGLISH, 0.0)
    vietnamese_score = scores.get(Language.VIETNAMESE, 0.0)
    return english_score >= minimum_confidence and english_score > vietnamese_score

def join_removal_reasons(row):
''',
        )
        source = source.replace(
            "    if row['is_too_long']:\n        reasons.append('over_200_words')\n",
            "    if row['is_too_long']:\n        reasons.append('over_200_words')\n"
            "    if row['is_english_comment']:\n        reasons.append('english_comment')\n",
        )
        source = source.replace(
            "    review_data['is_too_long'] = review_data['comment_word_count'].gt(200)\n",
            "    review_data['is_too_long'] = review_data['comment_word_count'].gt(200)\n"
            "    review_data['is_english_comment'] = review_data['comment'].map(\n"
            "        is_confident_english_comment\n"
            "    )\n",
        )
        cell['source'] = [source]

    if cell['cell_type'] == 'code' and source.startswith('# 5.3. Loại bỏ comment không hữu ích'):
        source = source.replace(
            "        'flagged_over_200_words',\n        'flagged_clear_advertising',",
            "        'flagged_over_200_words',\n        'flagged_english_comments',\n        'flagged_clear_advertising',",
        )
        source = source.replace(
            "        int(content_review['is_too_long'].sum()),\n        int(content_review['is_clear_ad'].sum()),",
            "        int(content_review['is_too_long'].sum()),\n"
            "        int(content_review['is_english_comment'].sum()),\n"
            "        int(content_review['is_clear_ad'].sum()),",
        )
        cell['source'] = [source]

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        cell['outputs'] = []
        cell['execution_count'] = None

nbformat.validate(nb)
path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('added high-confidence English comment filtering')
