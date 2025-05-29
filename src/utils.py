"""
Utility module for shared functionality across processors and analyzers.
"""

import re
from typing import Dict, List
import os

def extract_abbreviations_from_text(text: str, patterns: List[tuple]) -> Dict[str, str]:
    """
    Extract abbreviations and their definitions from text using provided patterns.

    Args:
        text (str): The text to analyze.
        patterns (List[tuple]): List of regex patterns and their types.

    Returns:
        Dict[str, str]: Dictionary of abbreviations and their definitions.
    """
    found_abbreviations = {}
    sentences = text.split('.')  # Split text into sentences using '.':

    for sentence in sentences:
        print(f"Processing sentence: {sentence.strip()}")  # Debugging output
        for pattern, pattern_type in patterns:
            matches = re.finditer(pattern, sentence)
            for match in matches:
                print(f"Match found: {match.groups()}")  # Debugging output
                if pattern_type == 'term_first':
                    term, abbr = match.groups()
                elif pattern_type == 'abbr_first':
                    abbr, term = match.groups()

                abbr = abbr.strip()
                term = term.strip()

                # Ensure abbreviation and term are valid
                if abbr.isupper() and len(abbr) > 1 and term and abbr not in found_abbreviations:
                    found_abbreviations[abbr] = term

    print(f"Extracted abbreviations: {found_abbreviations}")  # Debugging output
    return found_abbreviations

# Updated regex patterns
patterns = [
    (r'([A-Za-z][A-Za-z\s]+)\s*\(([A-Z]{2,})\)', 'term_first'),
    (r'([A-Z]{2,})\s*\(([A-Za-z][A-Za-z\s]+)\)', 'abbr_first')
]

def is_abbreviation_table(table) -> bool:
    """
    Check if a table is likely to contain abbreviations.

    Args:
        table: Table object to analyze.

    Returns:
        bool: True if the table is an abbreviation table.
    """
    if len(table.columns) == 2:
        header_cells = table.rows[0].cells
        if len(header_cells) >= 2:
            header_text = [cell.text.lower() for cell in header_cells]
            return 'abbreviation' in header_text and 'definition' in header_text
    return False

def sanitize_text(text: str) -> str:
    """Remove invalid XML characters from text."""
    return ''.join(c for c in text if c.isprintable() and c not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0B\x0C\x0E\x0F')
