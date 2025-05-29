"""
Unit tests for the shared utility module.
"""

import unittest
from src.utils import extract_abbreviations_from_text, is_abbreviation_table

class TestUtils(unittest.TestCase):

    def test_extract_abbreviations_from_text(self):
        text = "The patient was diagnosed with Chronic Kidney Disease (CKD) and Type 2 Diabetes (T2D)."
        patterns = [
            (r'([A-Za-z][A-Za-z\s\-]+?)\s*\(([A-Z][A-Z0-9\-]{1,})\)', 'term_first'),
            (r'([A-Z][A-Z0-9\-]{1,})\s*\(([A-Za-z][A-Za-z\s\-]+?)\)', 'abbr_first')
        ]
        result = extract_abbreviations_from_text(text, patterns)
        expected = {
            "CKD": "Chronic Kidney Disease",
            "T2D": "Type 2 Diabetes"
        }
        self.assertEqual(result, expected)

    def test_is_abbreviation_table(self):
        class MockCell:
            def __init__(self, text):
                self.text = text

        class MockRow:
            def __init__(self, cells):
                self.cells = cells

        class MockTable:
            def __init__(self, rows):
                self.rows = [MockRow(row) for row in rows]
                self.columns = [None, None]

        mock_table = MockTable([
            [MockCell("Abbreviation"), MockCell("Definition")],
            [MockCell("CKD"), MockCell("Chronic Kidney Disease")],
            [MockCell("T2D"), MockCell("Type 2 Diabetes")]
        ])

        self.assertTrue(is_abbreviation_table(mock_table))

if __name__ == "__main__":
    unittest.main()
