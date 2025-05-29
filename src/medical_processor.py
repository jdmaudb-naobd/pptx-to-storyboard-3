"""
Medical presentation content processor with intelligent structure detection
"""

import re
import json
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
import torch
from .abbreviation_database import MedicalAbbreviationDB
from .abbreviation_api import MedicalAbbreviationAPI
from .utils import extract_abbreviations_from_text

class MedicalContentProcessor:
    def __init__(self, abbreviations_file: str = "data/medical_abbreviations.json",
                 use_database: bool = True,
                 use_api: bool = True):
        self.chapters = []
        self.abbreviations = {}
        self.objectives = []
        self.embedding_model = None  # Load only when needed
        self.abbr_db = None
        self.abbr_api = None
        self.known_abbreviations = {}
        if Path(abbreviations_file).exists():
            with open(abbreviations_file, 'r', encoding='utf-8') as f:
                self.known_abbreviations = json.load(f)
        # Load ADAM abbreviation dictionary if available
        self.adam_abbr = {}
        adam_path = Path("data/ADAM_abbr.json")
        if adam_path.exists():
            with open(adam_path, encoding="utf-8") as f:
                self.adam_abbr = json.load(f)

        # <<< MOVE THIS BLOCK TO THE TOP OF __init__ >>>
        self.slide_type_patterns = {
            'title': {
                'patterns': [
                    r'^\s*$',  # Empty or minimal text
                    r'^[^.!?]{1,100}$',  # Short text without sentences
                ],
                'keywords': [],
                'max_words': 20,
                'priority': 1
            },
            'disclosure': {
                'patterns': [
                    r'disclos',
                    r'conflict\s+of\s+interest',
                    r'financial\s+relationship',
                    r'consulting\s+fee',
                    r'speaker\s+bureau',
                    r'advisory\s+board'
                ],
                'keywords': ['disclosure', 'conflict', 'financial', 'consulting'],
                'priority': 2
            },
            'objectives': {
                'patterns': [
                    r'learning\s+objectives?',
                    r'objectives?\s+(?:of|for)?\s+this',
                    r'(?:by|at)\s+the\s+end\s+of\s+this',
                    r'participants?\s+will\s+(?:be\s+able\s+to|learn)',
                    r'goals?\s+(?:of|for)?\s+this'
                ],
                'keywords': ['objective', 'goal', 'learn', 'understand'],
                'priority': 3
            },
            'patient_case': {
                'patterns': [
                    r'patient\s+(?:case|presentation)',
                    r'case\s+(?:study|presentation|report)',
                    r'\d+[-\s]?year[-\s]?old\s+(?:male|female|man|woman|patient)',
                    r'(?:presenting|presented)\s+with',
                    r'chief\s+complaint',
                    r'history\s+of\s+present\s+illness',
                    r'past\s+medical\s+history',
                    r'medications?',
                    r'allergies?'
                ],
                'keywords': ['patient', 'case', 'year-old', 'presented', 'history', 'complaint'],
                'priority': 4
            },
            'clinical_data': {
                'patterns': [
                    r'(?:clinical|study)\s+(?:trial|data|results)',
                    r'phase\s+[IVX123]',
                    r'efficacy',
                    r'safety',
                    r'adverse\s+events?',
                    r'statistical\s+analysis',
                    r'p[\s-]?value',
                    r'confidence\s+interval',
                    r'hazard\s+ratio',
                    r'endpoint'
                ],
                'keywords': ['trial', 'study', 'efficacy', 'safety', 'endpoint', 'analysis'],
                'priority': 5
            },
            'treatment': {
                'patterns': [
                    r'treatment\s+(?:options?|recommendations?|guidelines?)',
                    r'management',
                    r'therapy',
                    r'dosing',
                    r'administration',
                    r'mechanism\s+of\s+action',
                    r'pharmacokinetics?',
                    r'drug\s+interaction'
                ],
                'keywords': ['treatment', 'therapy', 'management', 'dosing', 'drug'],
                'priority': 6
            },
            'conclusion': {
                'patterns': [
                    r'conclusions?',
                    r'summary',
                    r'key\s+(?:points?|takeaways?|messages?)',
                    r'in\s+(?:conclusion|summary)',
                    r'take[\s-]?home\s+messages?'
                ],
                'keywords': ['conclusion', 'summary', 'key points', 'takeaway'],
                'priority': 7
            },
            'references': {
                'patterns': [
                    r'references?',
                    r'bibliography',
                    r'citations?',
                    r'sources?',
                    r'\d+\.\s+[A-Z][a-zA-Z]+.*\d{4}',  # Citation format
                    r'doi:\s*\S+',
                    r'https?://\S+'
                ],
                'keywords': ['reference', 'bibliography', 'citation'],
                'priority': 8
            },
            'questions': {
                'patterns': [
                    r'questions?\??',
                    r'q\s*&\s*a',
                    r'discussion',
                    r'thank\s+you',
                    r'contact\s+(?:information|me|us)'
                ],
                'keywords': ['question', 'thank you', 'contact', 'discussion'],
                'priority': 9
            }
        }
        # <<< END MOVE >>>

        if use_database:
            try:
                self.abbr_db = MedicalAbbreviationDB()
                stats = self.abbr_db.get_statistics()
                print(f"   Loaded abbreviation database: {stats['total_abbreviations']} entries")
            except Exception as e:
                print(f"   Warning: Could not load abbreviation database: {e}")

        if use_api:
            try:
                self.abbr_api = MedicalAbbreviationAPI()
                print("   Initialized medical abbreviation API handler")
            except Exception as e:
                print(f"   Warning: Could not initialize abbreviation API: {e}")
    def extract_abbreviations(self, content: Dict) -> Dict:
        """Enhanced abbreviation extraction with database/API lookup"""
        found_abbreviations = {}
        medical_patterns = [
            (r'([A-Za-z][A-Za-z\s\-]+?)\s*\(([A-Z][A-Z0-9\-]{1,})\)', 'term_first'),
            (r'([A-Z][A-Z0-9\-]{1,})\s*\(([A-Za-z][A-Za-z\s\-]+?)\)', 'abbr_first'),
            (r'([A-Z][A-Z0-9\-]{1,})\s*[=:]\s*([A-Za-z][A-Za-z\s\-]+)', 'abbr_equals')
        ]

        for slide in content["slides"]:
            for text_item in slide["texts"]:
                text = text_item["text"]
                abbreviations = extract_abbreviations_from_text(text, medical_patterns)
                found_abbreviations.update(abbreviations)

        return found_abbreviations
        # Define slide type patterns
        self.slide_type_patterns = {
            'title': {
                'patterns': [
                    r'^\s*$',  # Empty or minimal text
                    r'^[^.!?]{1,100}$',  # Short text without sentences
                ],
                'keywords': [],
                'max_words': 20,
                'priority': 1
            },
            'disclosure': {
                'patterns': [
                    r'disclos',
                    r'conflict\s+of\s+interest',
                    r'financial\s+relationship',
                    r'consulting\s+fee',
                    r'speaker\s+bureau',
                    r'advisory\s+board'
                ],
                'keywords': ['disclosure', 'conflict', 'financial', 'consulting'],
                'priority': 2
            },
            'objectives': {
                'patterns': [
                    r'learning\s+objectives?',
                    r'objectives?\s+(?:of|for)?\s+this',
                    r'(?:by|at)\s+the\s+end\s+of\s+this',
                    r'participants?\s+will\s+(?:be\s+able\s+to|learn)',
                    r'goals?\s+(?:of|for)?\s+this'
                ],
                'keywords': ['objective', 'goal', 'learn', 'understand'],
                'priority': 3
            },
            'patient_case': {
                'patterns': [
                    r'patient\s+(?:case|presentation)',
                    r'case\s+(?:study|presentation|report)',
                    r'\d+[-\s]?year[-\s]?old\s+(?:male|female|man|woman|patient)',
                    r'(?:presenting|presented)\s+with',
                    r'chief\s+complaint',
                    r'history\s+of\s+present\s+illness',
                    r'past\s+medical\s+history',
                    r'medications?',
                    r'allergies?'
                ],
                'keywords': ['patient', 'case', 'year-old', 'presented', 'history', 'complaint'],
                'priority': 4
            },
            'clinical_data': {
                'patterns': [
                    r'(?:clinical|study)\s+(?:trial|data|results)',
                    r'phase\s+[IVX123]',
                    r'efficacy',
                    r'safety',
                    r'adverse\s+events?',
                    r'statistical\s+analysis',
                    r'p[\s-]?value',
                    r'confidence\s+interval',
                    r'hazard\s+ratio',
                    r'endpoint'
                ],
                'keywords': ['trial', 'study', 'efficacy', 'safety', 'endpoint', 'analysis'],
                'priority': 5
            },
            'treatment': {
                'patterns': [
                    r'treatment\s+(?:options?|recommendations?|guidelines?)',
                    r'management',
                    r'therapy',
                    r'dosing',
                    r'administration',
                    r'mechanism\s+of\s+action',
                    r'pharmacokinetics?',
                    r'drug\s+interaction'
                ],
                'keywords': ['treatment', 'therapy', 'management', 'dosing', 'drug'],
                'priority': 6
            },
            'conclusion': {
                'patterns': [
                    r'conclusions?',
                    r'summary',
                    r'key\s+(?:points?|takeaways?|messages?)',
                    r'in\s+(?:conclusion|summary)',
                    r'take[\s-]?home\s+messages?'
                ],
                'keywords': ['conclusion', 'summary', 'key points', 'takeaway'],
                'priority': 7
            },
            'references': {
                'patterns': [
                    r'references?',
                    r'bibliography',
                    r'citations?',
                    r'sources?',
                    r'\d+\.\s+[A-Z][a-zA-Z]+.*\d{4}',  # Citation format
                    r'doi:\s*\S+',
                    r'https?://\S+'
                ],
                'keywords': ['reference', 'bibliography', 'citation'],
                'priority': 8
            },
            'questions': {
                'patterns': [
                    r'questions?\??',
                    r'q\s*&\s*a',
                    r'discussion',
                    r'thank\s+you',
                    r'contact\s+(?:information|me|us)'
                ],
                'keywords': ['question', 'thank you', 'contact', 'discussion'],
                'priority': 9
            }
        }
    
    def identify_structure(self, content: Dict) -> Dict:
        """Identify logical structure based on medical presentation patterns"""
        structure = {
            "chapters": [],
            "slide_types": {}  # Store slide type classifications
        }
        
        slides = content["slides"]
        
        # First pass: Classify each slide
        for slide in slides:
            slide_type = self._classify_slide(slide)
            structure["slide_types"][slide["slide_number"]] = slide_type
        
        # Second pass: Create logical chapters based on slide types
        chapters = self._create_logical_chapters(slides, structure["slide_types"])
        structure["chapters"] = chapters
        
        return structure
    
    def _classify_slide(self, slide: Dict) -> str:
        """Classify a slide based on its content"""
        all_text = " ".join([t["text"] for t in slide.get("texts", [])])
        text_lower = all_text.lower()
        
        # Score each slide type
        scores = {}
        
        for slide_type, config in self.slide_type_patterns.items():
            score = 0
            
            # Check patterns
            for pattern in config['patterns']:
                if re.search(pattern, text_lower):
                    score += 10
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword in text_lower:
                    score += 5
            
            # Special checks
            if slide_type == 'title':
                word_count = len(all_text.split())
                if word_count <= config['max_words'] and slide["slide_number"] <= 3:
                    score += 20
            
            if slide_type == 'references':
                # Check for multiple URLs or citations
                url_count = len(re.findall(r'https?://\S+', all_text))
                citation_count = len(re.findall(r'\d+\.\s+[A-Z][a-zA-Z]+.*\d{4}', all_text))
                score += (url_count + citation_count) * 5
            
            scores[slide_type] = score
        
        # Get the highest scoring type
        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return 'content'  # Default type
    
    def _create_logical_chapters(self, slides: List[Dict], slide_types: Dict[int, str]) -> List[Dict]:
        """Create logical chapters based on slide types"""
        chapters = []
        
        # Define the logical flow of a medical presentation
        chapter_definitions = [
            {
                'name': 'Introduction',
                'types': ['title', 'disclosure', 'objectives'],
                'optional': False
            },
            {
                'name': 'Patient Case',
                'types': ['patient_case'],
                'optional': True
            },
            {
                'name': 'Clinical Data & Evidence',
                'types': ['clinical_data'],
                'optional': True
            },
            {
                'name': 'Treatment & Management',
                'types': ['treatment'],
                'optional': True
            },
            {
                'name': 'Main Content',
                'types': ['content'],
                'optional': False
            },
            {
                'name': 'Conclusions',
                'types': ['conclusion', 'questions'],
                'optional': True
            },
            {
                'name': 'References',
                'types': ['references'],
                'optional': True
            }
        ]
        
        # Group slides by their position and type
        current_chapter = None
        processed_slides = set()
        
        for chapter_def in chapter_definitions:
            chapter_slides = []
            
            # Find slides matching this chapter's types
            for slide_num, slide_type in slide_types.items():
                if slide_type in chapter_def['types'] and slide_num not in processed_slides:
                    chapter_slides.append(slide_num)
                    processed_slides.add(slide_num)
            
            # Create chapter if we have slides or if it's not optional
            if chapter_slides or not chapter_def['optional']:
                # If no slides but required, check if we have unprocessed content slides
                if not chapter_slides and chapter_def['name'] == 'Main Content':
                    # Add all remaining unprocessed slides
                    for slide_num in range(1, len(slides) + 1):
                        if slide_num not in processed_slides:
                            chapter_slides.append(slide_num)
                            processed_slides.add(slide_num)
                
                if chapter_slides:
                    chapter = {
                        'title': chapter_def['name'],
                        'slide_number': min(chapter_slides),
                        'slides': sorted(chapter_slides),
                        'subchapters': []
                    }
                    
                    # For main content, try to identify subchapters
                    if chapter_def['name'] == 'Main Content' and len(chapter_slides) > 5:
                        subchapters = self._identify_content_subchapters(
                            slides, chapter_slides, slide_types
                        )
                        chapter['subchapters'] = subchapters
                    
                    chapters.append(chapter)
        
        # Handle any remaining unprocessed slides
        remaining = set(range(1, len(slides) + 1)) - processed_slides
        if remaining:
            chapters.append({
                'title': 'Additional Content',
                'slide_number': min(remaining),
                'slides': sorted(remaining),
                'subchapters': []
            })
        
        return chapters
    
    def _identify_content_subchapters(self, slides: List[Dict], 
                                    slide_numbers: List[int], 
                                    slide_types: Dict[int, str]) -> List[Dict]:
        """Identify subchapters within main content based on topic changes"""
        subchapters = []
        
        # Look for natural breaks or topic changes
        current_subchapter = None
        current_topic_slides = []
        
        for slide_num in sorted(slide_numbers):
            slide = slides[slide_num - 1]
            
            # Check if this slide looks like a section header
            if self._is_section_header(slide):
                # Save previous subchapter
                if current_topic_slides:
                    if current_subchapter:
                        current_subchapter['slides'] = current_topic_slides
                        subchapters.append(current_subchapter)
                
                # Start new subchapter
                title = self._extract_section_title(slide)
                current_subchapter = {
                    'title': title,
                    'slide_number': slide_num,
                    'slides': []
                }
                current_topic_slides = [slide_num]
            else:
                current_topic_slides.append(slide_num)
        
        # Add last subchapter
        if current_subchapter and current_topic_slides:
            current_subchapter['slides'] = current_topic_slides
            subchapters.append(current_subchapter)
        
        return subchapters
    
    def _is_section_header(self, slide: Dict) -> bool:
        """Check if a slide appears to be a section header"""
        texts = slide.get("texts", [])
        
        if not texts:
            return False
        
        # Section headers typically have:
        # - Minimal text (1-3 text elements)
        # - No bullet points
        # - Shorter total length
        # - Often centered or title-formatted
        
        if len(texts) > 3:
            return False
        
        all_text = " ".join([t["text"] for t in texts])
        
        # Check for bullet points
        if self._has_bullet_points(all_text):
            return False
        
        # Check length
        word_count = len(all_text.split())
        if word_count > 15:
            return False
        
        # Check if it has a title
        has_title = any(t.get("is_title", False) for t in texts)
        
        return has_title or word_count < 10
    
    def _extract_section_title(self, slide: Dict) -> str:
        """Extract section title from a slide"""
        texts = slide.get("texts", [])
        
        # Prefer text marked as title
        for text in texts:
            if text.get("is_title", False):
                return text["text"].strip()
        
        # Otherwise, use first non-empty text
        for text in texts:
            if text["text"].strip():
                return text["text"].strip()
        
        return f"Section {slide['slide_number']}"
    
    def _has_bullet_points(self, text: str) -> bool:
        """Check if text contains bullet points"""
        bullet_patterns = [
            r'^\s*[•·▪▸→-]\s+',
            r'^\s*\d+\.\s+',
            r'^\s*[a-zA-Z]\.\s+',
            r'^\s*\([a-zA-Z0-9]\)\s+'
        ]
        
        lines = text.split('\n')
        bullet_count = sum(
            1 for line in lines
            if any(re.match(pattern, line) for pattern in bullet_patterns)
        )
        
        return bullet_count >= 2  # At least 2 bullet points
    
    def extract_abbreviations(self, content: Dict) -> Dict:
        """Enhanced medical abbreviation extraction with lookup"""
        found_abbreviations = {}
        all_abbreviations_in_text = set()
        
        # Medical-specific abbreviation patterns
        medical_patterns = [
            # Standard patterns
            (r'([A-Za-z][A-Za-z\s\-]+?)\s*\(([A-Z][A-Z0-9\-]{1,})\)', 'term_first'),
            (r'([A-Z][A-Z0-9\-]{1,})\s*\(([A-Za-z][A-Za-z\s\-]+?)\)', 'abbr_first'),
            # Medical notation patterns
            (r'([A-Z][A-Z0-9\-]{1,})\s*[=:]\s*([A-Za-z][A-Za-z\s\-]+)', 'abbr_equals'),
            # Dosing abbreviations
            (r'\b([A-Z]{2,4})\b(?=\s*(?:daily|twice|three times|four times))', 'dosing'),
            # Lab values
            (r'\b([A-Z]{2,4})\b(?=\s*(?:\d+\.?\d*|<|>|≤|≥))', 'lab_value'),
        ]
        
        for slide in content["slides"]:
            for text_item in slide["texts"]:
                text = text_item["text"]
                
                # Find defined abbreviations
                for pattern, pattern_type in medical_patterns[:3]:  # First 3 are definition patterns
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        if pattern_type == 'term_first':
                            term, abbr = match.groups()
                        else:
                            abbr, term = match.groups()
                        
                        abbr = abbr.strip()
                        term = term.strip()
                        
                        if self._is_valid_medical_abbreviation(abbr) and term:
                            found_abbreviations[abbr] = term
                
                # Find all potential abbreviations
                potential_abbrs = re.findall(r'\b([A-Z][A-Z0-9\-]{1,6})\b', text)
                all_abbreviations_in_text.update(potential_abbrs)
        
        # Add known medical abbreviations that appear in text
        for abbr in all_abbreviations_in_text:
            if abbr not in found_abbreviations:
                if abbr in self.known_abbreviations:
                    found_abbreviations[abbr] = self.known_abbreviations[abbr]
                elif abbr in self.adam_abbr:
                    defs = self.adam_abbr[abbr]
                    found_abbreviations[abbr] = defs[0] if isinstance(defs, list) else defs
        
        # For undefined abbreviations, attempt to lookup or mark as undefined
        undefined_abbrs = []
        for abbr in all_abbreviations_in_text:
            if abbr not in found_abbreviations and self._is_valid_medical_abbreviation(abbr):
                # Try context-based lookup
                definition = self._lookup_medical_abbreviation(abbr, content)
                if definition:
                    found_abbreviations[abbr] = definition
                else:
                    found_abbreviations[abbr] = "(Not defined - please verify)"
                    undefined_abbrs.append(abbr)
        
        # Print undefined abbreviations for user awareness
        if undefined_abbrs:
            print(f"\n   ⚠ Found undefined abbreviations: {', '.join(sorted(undefined_abbrs))}")
            print(f"     Consider adding definitions to medical_abbreviations.json")
        
        return found_abbreviations
    
    def _is_valid_medical_abbreviation(self, text: str) -> bool:
        """Check if text is a valid medical abbreviation"""
        # Must be 2-6 characters (medical abbreviations are typically short)
        if len(text) < 2 or len(text) > 6:
            return False
        
        # Allow letters, numbers, and hyphens
        if not re.match(r'^[A-Z][A-Z0-9\-]*$', text):
            return False
        
        # Exclude common words and Roman numerals
        excluded = {
            'IS', 'IT', 'OF', 'TO', 'IN', 'OR', 'AN', 'AS', 'AT', 'BY', 'WE', 'ME', 'US',
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'NO', 'YES', 'OK', 'THE', 'AND', 'FOR', 'ARE', 'CAN', 'HAS', 'BUT'
        }
        if text in excluded:
            return False
        
        return True
    
    def _lookup_medical_abbreviation(self, abbr: str, content: Dict) -> Optional[str]:
        """Attempt to find definition for abbreviation using context"""
        # Common medical abbreviation patterns based on context
        context_definitions = {
            # Dosing frequencies
            'QD': 'once daily',
            'BID': 'twice daily',
            'TID': 'three times daily',
            'QID': 'four times daily',
            'PRN': 'as needed',
            'QHS': 'at bedtime',
            # Common medical terms
            'VS': 'vital signs',
            'WNL': 'within normal limits',
            'NAD': 'no acute distress',
            'NKA': 'no known allergies',
            'NKDA': 'no known drug allergies',
            # Units
            'MG': 'milligrams',
            'ML': 'milliliters',
            'MCG': 'micrograms',
        }
        
        # Check context-based definitions
        if abbr in context_definitions:
            return context_definitions[abbr]
        
        # Could implement more sophisticated lookup here
        # For now, return None to indicate not found
        return None
    
    def extract_objectives(self, content: Dict) -> List[str]:
        """Extract learning objectives with medical presentation awareness"""
        objectives = []
        
        # Look for objectives slides
        for slide in content["slides"]:
            slide_text = " ".join([t["text"].lower() for t in slide["texts"]])
            
            # Check if this is an objectives slide
            is_objective_slide = any(
                re.search(pattern, slide_text) 
                for pattern in self.slide_type_patterns['objectives']['patterns']
            )
            
            if is_objective_slide:
                # Extract individual objectives
                for text_item in slide["texts"]:
                    text = text_item["text"].strip()
                    
                    # Skip titles
                    if text_item.get("is_title", False):
                        continue
                    
                    # Clean up bullet points and numbers
                    text = re.sub(r'^[\s•·▪▸→\-\*\d\.]+', '', text).strip()
                    
                    # Add if it's substantial text
                    if text and len(text.split()) > 3:
                        objectives.append(text)
        
        return objectives
    
    def extract_references(self, content: Dict) -> Dict[int, List[str]]:
        """Extract references with enhanced medical citation detection"""
        slide_references = {}
        
        # Medical citation patterns
        citation_patterns = [
            # Standard URLs
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'www\.[^\s<>"{}|\\^`\[\]]+',
            # DOIs
            r'(?:doi:\s*|https?://doi\.org/)[\S]+',
            r'10\.\d{4,}/[\S]+',
            # PubMed IDs
            r'PMID:\s*\d+',
            r'PMC\d+',
            # Medical journal citations
            r'[A-Z][a-zA-Z\-]+\s+et\s+al\.?,?\s+[A-Z][a-zA-Z\s]+\.?\s+\d{4}',
            r'[A-Z][a-zA-Z\-]+\s+et\s+al\.?,?\s+\d{4}',
            # Journal abbreviations with year
            r'(?:NEJM|JAMA|BMJ|Lancet|JACC|JCO|Blood|Nature|Science|Cell)\s+\d{4}',
            # Clinical trial identifiers
            r'NCT\d{8}',
            r'ISRCTN\d{8}',
            # Guidelines
            r'(?:AHA|ACC|ESC|NCCN|ASCO|FDA|EMA)\s+(?:guidelines?|guidance|recommendation)',
        ]
        
        combined_pattern = '|'.join(f'({pattern})' for pattern in citation_patterns)
        
        for slide in content["slides"]:
            refs = []
            for text_item in slide["texts"]:
                matches = re.finditer(combined_pattern, text_item["text"], re.IGNORECASE)
                for match in matches:
                    ref = match.group(0).strip()
                    if ref:
                        refs.append(ref)
            
            if refs:
                slide_references[slide["slide_number"]] = refs
        
        return slide_references