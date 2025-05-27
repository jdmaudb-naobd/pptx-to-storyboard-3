"""
Process extracted content into structured format
"""

import re
from typing import Dict, List
from sentence_transformers import SentenceTransformer, util

class ContentProcessor:
    def __init__(self):
        self.chapters = []
        self.abbreviations = {}
        self.objectives = []
        # Load the model (first time will download)
        self.embedding_model = SentenceTransformer("BAAI/bge-m3")
        
    def identify_structure(self, content: Dict) -> Dict:
        """Identify chapters and structure from slides, robust to variation and title slides"""
        structure = {
            "chapters": [],
            "current_chapter": None,
            "current_subchapter": None
        }

        slides = content["slides"]
        assigned = set()

        for idx, slide in enumerate(slides):
            slide_text = " ".join([t["text"] for t in slide["texts"]])

            # Check for chapter indicators
            if self._is_chapter_slide(slide_text):
                chapter = {
                    "title": self._extract_chapter_title(slide_text),
                    "slide_number": slide["slide_number"],
                    "slides": [slide["slide_number"]],
                    "subchapters": []
                }
                structure["chapters"].append(chapter)
                structure["current_chapter"] = chapter
                structure["current_subchapter"] = None
                assigned.add(slide["slide_number"])

            # Check for subchapter indicators
            elif self._is_subchapter_slide(slide_text):
                if structure["current_chapter"]:
                    subchapter = {
                        "title": self._extract_subchapter_title(slide_text),
                        "slide_number": slide["slide_number"],
                        "slides": [slide["slide_number"]]
                    }
                    structure["current_chapter"]["subchapters"].append(subchapter)
                    structure["current_subchapter"] = subchapter
                    assigned.add(slide["slide_number"])

            # Regular content slide
            else:
                if structure["current_subchapter"]:
                    structure["current_subchapter"]["slides"].append(slide["slide_number"])
                    assigned.add(slide["slide_number"])
                elif structure["current_chapter"]:
                    structure["current_chapter"]["slides"].append(slide["slide_number"])
                    assigned.add(slide["slide_number"])

        # If first slide is not a chapter, treat as Title Slide chapter
        if slides and slides[0]["slide_number"] not in assigned:
            structure["chapters"].insert(0, {
                "title": "Title Slide",
                "slide_number": slides[0]["slide_number"],
                "slides": [slides[0]["slide_number"]],
                "subchapters": []
            })
            assigned.add(slides[0]["slide_number"])

        # Fallback: If no chapters found, create a default chapter with all slides
        if not structure["chapters"]:
            structure["chapters"].append({
                "title": "All Slides",
                "slide_number": slides[0]["slide_number"] if slides else 1,
                "slides": [slide["slide_number"] for slide in slides],
                "subchapters": []
            })
        else:
            # Add any unassigned slides to the last chapter
            unassigned = [slide["slide_number"] for slide in slides if slide["slide_number"] not in assigned]
            if unassigned:
                structure["chapters"][-1]["slides"].extend(unassigned)

        return structure
    
    def extract_abbreviations(self, content: Dict) -> Dict:
        """Extract abbreviations from all slides, using multiple patterns and collecting all matches."""
        abbreviations = {}
        # Patterns for definitions like: Full Term (ABBR), ABBR (Full Term), ABBR = Full Term, ABBR: Full Term, etc.
        patterns = [
            r'([A-Za-z][A-Za-z\s]+?)\s*\(([A-Z]{2,})\)',      # Full Term (ABBR)
            r'([A-Z]{2,})\s*\(([A-Za-z][A-Za-z\s]+?)\)',      # ABBR (Full Term)
            r'([A-Z]{2,})\s*[:=]\s*([A-Za-z][A-Za-z\s]+)',    # ABBR: Full Term or ABBR = Full Term
            r'([A-Za-z][A-Za-z\s]+?)\s*[:=]\s*([A-Z]{2,})',   # Full Term: ABBR or Full Term = ABBR
            r'([A-Z]{2,})\s+(?:stands for|means)\s+([A-Za-z][A-Za-z\s]+)',  # ABBR stands for Full Term
            r'([A-Za-z][A-Za-z\s]+?)\s+(?:is abbreviated as|abbreviated as)\s+([A-Z]{2,})', # Full Term is abbreviated as ABBR
        ]
        for slide in content["slides"]:
            for text_item in slide["texts"]:
                text = text_item["text"]
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        # Normalize match order based on pattern
                        if pattern in [patterns[0], patterns[3], patterns[5]]:
                            term, abbr = match
                        else:
                            abbr, term = match
                        abbr = abbr.strip()
                        term = term.strip()
                        if abbr and term and abbr.isupper() and len(abbr) > 1:
                            abbreviations[abbr] = term

        # Optionally, comment out the following block if you only want defined abbreviations:
        all_text = " ".join(
            text_item["text"] for slide in content["slides"] for text_item in slide["texts"]
        )
        possible_abbrs = set(re.findall(r'\b([A-Z]{2,})\b', all_text))
        for abbr in possible_abbrs:
            if abbr not in abbreviations:
                abbreviations[abbr] = "(Not defined in slides)"

        return abbreviations
    
    def extract_objectives(self, content: Dict) -> List[str]:
        """Extract learning objectives"""
        objectives = []
        objective_keywords = ["objective", "goal", "learn", "understand", "able to"]
        for slide in content["slides"]:
            slide_text = " ".join([t["text"].lower() for t in slide["texts"]])
            if any(keyword in slide_text for keyword in objective_keywords):
                for text_item in slide["texts"]:
                    text = text_item["text"].strip()
                    if text and not text_item.get("is_title", False):
                        text = re.sub(r'^[\s•·\-\*]+', '', text)
                        if text:
                            objectives.append(text)
        return objectives
    
    def _is_chapter_slide(self, text: str) -> bool:
        """Check if slide represents a chapter"""
        chapter_patterns = [
            r'chapter\s+\d+',
            r'module\s+\d+',
            r'section\s+\d+',
            r'unit\s+\d+'
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in chapter_patterns)
    
    def _is_subchapter_slide(self, text: str) -> bool:
        """Check if slide represents a subchapter"""
        subchapter_patterns = [
            r'part\s+\d+',
            r'topic\s+\d+',
            r'lesson\s+\d+'
        ]
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in subchapter_patterns)
    
    def _extract_chapter_title(self, text: str) -> str:
        """Extract chapter title from text"""
        lines = text.strip().split('\n')
        return lines[0] if lines else "Untitled Chapter"

    def _extract_subchapter_title(self, text: str) -> str:
        """Extract subchapter title from text"""
        lines = text.strip().split('\n')
        return lines[0] if lines else "Untitled Subchapter"

    def find_abbreviation_definitions(self, content: Dict) -> Dict:
        """Use embeddings to find best definition for each abbreviation."""
        all_texts = []
        for slide in content["slides"]:
            for text_item in slide["texts"]:
                all_texts.append(text_item["text"])

        # Find all candidate abbreviations (all-caps words)
        all_text = " ".join(all_texts)
        possible_abbrs = set(re.findall(r'\b([A-Z]{2,})\b', all_text))

        # Get embeddings for all sentences
        sentence_embeddings = self.embedding_model.encode(all_texts, convert_to_tensor=True)

        abbr_defs = {}
        for abbr in possible_abbrs:
            # For each abbreviation, find the sentence most similar to "Definition of ABBR"
            query = f"Definition of {abbr}"
            query_emb = self.embedding_model.encode(query, convert_to_tensor=True)
            cos_scores = util.cos_sim(query_emb, sentence_embeddings)[0]
            best_idx = int(cos_scores.argmax())
            best_sentence = all_texts[best_idx]
            abbr_defs[abbr] = best_sentence


        return abbr_defs
        return abbr_defs