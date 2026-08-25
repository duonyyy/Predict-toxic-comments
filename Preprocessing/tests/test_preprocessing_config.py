import json
import re
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_DIR / 'config' / 'preprocessing_config.json'
NOTEBOOK_PATH = PROJECT_DIR / 'notebooks' / '02_clearing_data.ipynb'


class PreprocessingRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        cls.config = config

        notebook = json.loads(NOTEBOOK_PATH.read_text(encoding='utf-8'))
        regex_cell = next(
            ''.join(cell.get('source', []))
            for cell in notebook['cells']
            if "URL_RE = re.compile" in ''.join(cell.get('source', []))
        )
        namespace = {'re': re}
        exec(regex_cell, namespace)
        cls.rules = namespace

    def test_config_has_safe_thresholds(self):
        self.assertEqual(self.config['min_comment_words'], 2)
        self.assertGreater(self.config['max_comment_words'], self.config['min_comment_words'])
        self.assertGreaterEqual(self.config['semantic_similarity_threshold'], 0.9)

    def test_phone_formats_are_detected(self):
        pattern = self.rules['PHONE_RE']
        for value in ['090 123 4567', '090-123-4567', '+84 901234567']:
            self.assertIsNotNone(pattern.search(value), value)

    def test_domain_email_and_unicode_mention_are_detected(self):
        self.assertIsNotNone(self.rules['URL_RE'].search('xem vnexpress.net'))
        self.assertIsNotNone(self.rules['EMAIL_RE'].search('abc@example.com'))
        self.assertIsNotNone(self.rules['MENTION_RE'].search('@người_dùng'))


if __name__ == '__main__':
    unittest.main()
