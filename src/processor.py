import re
import json
import requests
from typing import List, Dict, Optional

class Processor:
    def __init__(self, doc):
        self.doc = doc
        self.local_abbreviations = self.load_local_abbreviations()
        self.external_abbreviations = self.load_external_abbreviations()

    def detect_abbreviations(self, text: str) -> List[str]:
        """Detect abbreviations in text using regex."""
        abbreviation_pattern = r'\b[A-Z]{2,}\b'  # Matches all-caps words (2+ letters)
        return re.findall(abbreviation_pattern, text)

    def extract_abbreviations(self, content: Dict) -> Dict[str, str]:
        """Extract abbreviations from all slides."""
        abbreviations = {}
        for slide in content["slides"]:
            for text_item in slide["texts"]:
                detected_abbrs = self.detect_abbreviations(text_item["text"])
                for abbr in detected_abbrs:
                    if abbr not in abbreviations:
                        abbreviations[abbr] = self.get_abbreviation_definition(abbr)
        return abbreviations

    def query_external_api(self, abbr: str) -> Optional[str]:
        """Query external API for abbreviation definition."""
        api_url = f"https://api.example.com/abbreviations/{abbr}"  # Replace with actual API URL
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            return data.get("definition")
        return None

    def get_abbreviation_definition(self, abbr: str) -> str:
        """Find the definition for an abbreviation."""
        if abbr in self.local_abbreviations:
            return self.local_abbreviations[abbr]
        elif abbr in self.external_abbreviations:
            return self.external_abbreviations[abbr][0] if isinstance(self.external_abbreviations[abbr], list) else self.external_abbreviations[abbr]
        else:
            # Query external API for definition
            definition = self.query_external_api(abbr)
            return definition if definition else "(Not defined - please verify)"

    def load_local_abbreviations(self) -> Dict[str, str]:
        """Load local abbreviation dictionary."""
        # Example: Load from abbreviations.json
        with open("data/abbreviations.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def load_external_abbreviations(self) -> Dict[str, List[str]]:
        """Load external abbreviation dictionary."""
        # Example: Load from ADAM or other external sources
        with open("data/ADAM_abbr.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def create_abbreviations_table(self, abbreviations: Dict[str, str]) -> None:
        """Generate the abbreviations table."""
        table = self.doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        table.rows[0].cells[0].text = "Abbreviation"
        table.rows[0].cells[1].text = "Definition"

        for abbr, definition in abbreviations.items():
            row = table.add_row()
            row.cells[0].text = abbr
            row.cells[1].text = definition

    # Removed redundant code and centralized abbreviation loading.