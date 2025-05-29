"""
Example Analyzer - Learns patterns from input/output storyboard pairs
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
from docx import Document
import difflib

# Import existing modules
from src.extractor import SimpleExtractor
from src.medical_processor import MedicalContentProcessor


class StoryboardAnalyzer:
    """Analyzes storyboard documents to extract structure and content"""
    
    def __init__(self, docx_path: str):
        self.doc = Document(docx_path)
        self.structure = self.extract_structure()
        
    def extract_structure(self) -> Dict:
        """Extract the structure from a storyboard document"""
        structure = {
            'chapters': [],
            'abbreviations': {},
            'segments': [],
            'questions': []
        }
        
        current_chapter = None
        current_subchapter = None
        
        # Track what we're currently parsing
        in_abbreviations = False
        current_segment = None
        current_question = None
        
        for element in self.doc.element.body:
            if element.tag.endswith('tbl'):
                # Handle tables
                table = self._parse_table(element)
                
                if self._is_abbreviations_table(table):
                    structure['abbreviations'] = self._extract_abbreviations(table)
                elif self._is_segment_table(table):
                    segment = self._extract_segment(table)
                    if current_chapter:
                        segment['chapter'] = current_chapter
                    if current_subchapter:
                        segment['subchapter'] = current_subchapter
                    structure['segments'].append(segment)
                elif self._is_question_table(table):
                    question = self._extract_question(table)
                    if current_chapter:
                        question['chapter'] = current_chapter
                    if current_subchapter:
                        question['subchapter'] = current_subchapter
                    structure['questions'].append(question)
                    
            elif element.tag.endswith('p'):
                # Handle paragraphs (headings)
                para = self._get_paragraph_text(element)
                if para:
                    # Check if it's a chapter or subchapter based on the styles found
                    style_name = self._get_paragraph_style(element)
                    
                    # Based on your document analysis:
                    # Heading 1 = Chapter
                    # AX Subhead = Subchapter
                    if style_name == 'Heading 1':
                        current_chapter = para
                        current_subchapter = None
                        structure['chapters'].append({
                            'title': para,
                            'subchapters': []
                        })
                    elif style_name == 'AX Subhead':
                        current_subchapter = para
                        if structure['chapters']:
                            structure['chapters'][-1]['subchapters'].append(para)
        
        return structure
    
    def _parse_table(self, table_element) -> List[List[str]]:
        """Parse a table element into a 2D list of strings"""
        rows = []
        for row in table_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'):
            cells = []
            for cell in row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                text = self._get_cell_text(cell)
                cells.append(text)
            rows.append(cells)
        return rows
    
    def _get_cell_text(self, cell) -> str:
        """Extract text from a table cell"""
        texts = []
        for p in cell.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            text = self._get_paragraph_text(p)
            if text:
                texts.append(text)
        return '\n'.join(texts)
    
    def _get_paragraph_text(self, para) -> str:
        """Extract text from a paragraph element"""
        texts = []
        for r in para.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
            for t in r.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                if t.text:
                    texts.append(t.text)
        return ''.join(texts)
    
    def _get_paragraph_style(self, para) -> str:
        """Get the style of a paragraph"""
        style_elem = para.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle')
        if style_elem is not None:
            return style_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
        return 'Normal'  # Default to Normal if no style specified
    
    def _is_abbreviations_table(self, table: List[List[str]]) -> bool:
        """Check if a table is an abbreviations table"""
        if len(table) > 0:
            # Based on your data: abbreviation tables are typically Nx2 format
            if len(table[0]) == 2:
                # Check header or first few rows for abbreviation-like content
                header = table[0] if table else []
                # Look for "abbreviation" in header or check if content looks like abbreviations
                if any('abbreviation' in cell.lower() for cell in header):
                    return True
                # Check if first column has short uppercase text (typical abbreviations)
                if len(table) > 3:
                    first_col_texts = [row[0] for row in table[1:4] if len(row) > 0]
                    uppercase_count = sum(1 for text in first_col_texts if text.isupper() and len(text) < 10)
                    if uppercase_count >= 2:
                        return True
        return False
    
    def _is_segment_table(self, table: List[List[str]]) -> bool:
        """Check if a table is a content segment table"""
        if len(table) > 0:
            # Based on your data: segment tables are typically Nx3 or Nx4 format
            num_cols = len(table[0]) if table[0] else 0
            if num_cols in [3, 4]:
                # Look for typical segment table fields in first column
                first_col = [row[0].lower() if row and len(row) > 0 else '' for row in table]
                segment_fields = ['chapter', 'subchapter', 'text', 'visual', 'graphic', 
                                'interactivity', 'references', 'note', 'setting']
                matches = sum(1 for field in segment_fields if any(field in cell for cell in first_col))
                return matches >= 2  # At least 2 matching fields
        return False
    
    def _is_question_table(self, table: List[List[str]]) -> bool:
        """Check if a table is a question table"""
        if len(table) > 0:
            first_col = [row[0].lower() if row else '' for row in table]
            question_fields = ['question', 'answer', 'feedback', 'solution']
            matches = sum(1 for field in question_fields if any(field in cell for cell in first_col))
            return matches >= 2
        return False
    
    def _extract_abbreviations(self, table: List[List[str]]) -> Dict[str, str]:
        """Extract abbreviations from an abbreviations table"""
        abbrevs = {}
        for i, row in enumerate(table):
            if i == 0:  # Skip header
                continue
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                abbrevs[row[0].strip()] = row[1].strip()
        return abbrevs
    
    def _extract_segment(self, table: List[List[str]]) -> Dict:
        """Extract content from a segment table"""
        segment = {}
        for row in table:
            if len(row) >= 2:
                field = row[0].lower().strip()
                value = row[1].strip() if len(row) > 1 else ''
                
                if 'chapter' in field:
                    segment['chapter'] = value
                elif 'subchapter' in field:
                    segment['subchapter'] = value
                elif 'text' in field:
                    segment['text'] = value
                elif 'visual' in field or 'graphic' in field:
                    segment['visuals'] = value
                elif 'interactivity' in field:
                    segment['interactivity'] = value
                elif 'reference' in field:
                    segment['references'] = value
                elif 'note' in field or 'setting' in field:
                    segment['notes'] = value
        
        return segment
    
    def _extract_question(self, table: List[List[str]]) -> Dict:
        """Extract content from a question table"""
        question = {}
        for row in table:
            if len(row) >= 2:
                field = row[0].lower().strip()
                value = row[1].strip() if len(row) > 1 else ''
                
                if 'chapter' in field:
                    question['chapter'] = value
                elif 'subchapter' in field:
                    question['subchapter'] = value
                elif 'text' in field and 'feedback' not in field:
                    question['text'] = value
                elif 'answer' in field and 'feedback' not in field:
                    question['answers'] = value
                elif 'feedback' in field:
                    question['feedback'] = value
                elif 'solution' in field:
                    question['solution'] = value
                elif 'reference' in field:
                    question['references'] = value
        
        return question


class ExampleAnalyzer:
    """Analyzes input/output pairs to learn transformation patterns"""
    
    def __init__(self, examples_dir: str = "examples"):
        self.examples_dir = Path(examples_dir)
        self.patterns = {
            'slide_to_section_mappings': defaultdict(list),
            'slide_combinations': [],
            'slide_omissions': [],
            'content_transformations': [],
            'structure_patterns': [],
            'abbreviation_patterns': []
        }
        self.medical_processor = MedicalContentProcessor()
        
    def analyze_all_examples(self) -> Dict:
        """Analyze all example pairs and extract patterns"""
        print("Starting Example Analysis...")
        print("=" * 60)
        
        # Get all project folders
        input_dir = self.examples_dir / "input"
        output_dir = self.examples_dir / "output"
        
        if not input_dir.exists() or not output_dir.exists():
            print(f"Error: Could not find input/output directories in {self.examples_dir}")
            return {}
        
        projects = [d.name for d in input_dir.iterdir() if d.is_dir()]
        print(f"Found {len(projects)} projects to analyze")
        
        all_results = []
        
        for project in projects:
            print(f"\nAnalyzing project: {project}")
            print("-" * 40)
            
            # Find matching files
            input_files = list((input_dir / project).glob("*.pptx"))
            output_files = list((output_dir / project).glob("*.docx"))
            
            for input_file in input_files:
                # Find matching output file
                matching_output = None
                for output_file in output_files:
                    if input_file.stem == output_file.stem:
                        matching_output = output_file
                        break
                
                if matching_output:
                    print(f"  Analyzing pair: {input_file.name} <-> {matching_output.name}")
                    result = self.analyze_pair(input_file, matching_output)
                    all_results.append(result)
                else:
                    print(f"  Warning: No matching output for {input_file.name}")
        
        # Aggregate patterns across all examples
        aggregated_patterns = self.aggregate_patterns(all_results)
        
        # Generate report
        self.generate_report(aggregated_patterns)
        
        return aggregated_patterns
    
    def analyze_pair(self, pptx_path: Path, docx_path: Path) -> Dict:
        """Analyze a single input/output pair"""
        # Extract content from PowerPoint
        extractor = SimpleExtractor(pptx_path)
        pptx_content = extractor.extract_all_content()
        
        # Analyze PowerPoint structure
        pptx_structure = self.medical_processor.identify_structure(pptx_content)
        
        # Extract content from storyboard
        storyboard = StoryboardAnalyzer(str(docx_path))
        
        # Analyze transformations
        transformations = self.analyze_transformations(
            pptx_content, 
            pptx_structure, 
            storyboard.structure
        )
        
        return {
            'project': pptx_path.parent.name,
            'file': pptx_path.name,
            'pptx_content': pptx_content,
            'pptx_structure': pptx_structure,
            'storyboard_structure': storyboard.structure,
            'transformations': transformations
        }
    
    def analyze_transformations(self, pptx_content: Dict, pptx_structure: Dict, 
                               storyboard_structure: Dict) -> Dict:
        """Analyze how slides were transformed into storyboard sections"""
        transformations = {
            'slide_mappings': [],
            'omitted_slides': [],
            'combined_slides': [],
            'structure_mapping': {},
            'content_changes': []
        }
        
        # Extract all text from slides for matching
        slide_texts = {}
        for slide in pptx_content['slides']:
            slide_num = slide['slide_number']
            all_text = ' '.join([t['text'] for t in slide.get('texts', [])])
            slide_texts[slide_num] = all_text
        
        # Extract all text from storyboard segments
        segment_texts = []
        for segment in storyboard_structure['segments']:
            segment_texts.append({
                'text': segment.get('text', ''),
                'chapter': segment.get('chapter', ''),
                'subchapter': segment.get('subchapter', ''),
                'full_segment': segment
            })
        
        # Try to match slides to segments
        matched_slides = set()
        
        for segment in segment_texts:
            segment_text = segment['text'].lower()
            matching_slides = []
            
            # Find slides that match this segment
            for slide_num, slide_text in slide_texts.items():
                if slide_text and segment_text:
                    # Calculate similarity
                    similarity = self._calculate_similarity(slide_text.lower(), segment_text)
                    if similarity > 0.3:  # Threshold for matching
                        matching_slides.append((slide_num, similarity))
            
            if matching_slides:
                # Sort by similarity
                matching_slides.sort(key=lambda x: x[1], reverse=True)
                slide_nums = [s[0] for s in matching_slides]
                
                transformations['slide_mappings'].append({
                    'slides': slide_nums,
                    'chapter': segment['chapter'],
                    'subchapter': segment['subchapter'],
                    'segment_preview': segment_text[:100] + '...' if len(segment_text) > 100 else segment_text
                })
                
                matched_slides.update(slide_nums)
                
                # Check if multiple slides were combined
                if len(slide_nums) > 1:
                    transformations['combined_slides'].append({
                        'slides': slide_nums,
                        'into': f"{segment['chapter']} - {segment['subchapter']}"
                    })
        
        # Find omitted slides
        all_slides = set(range(1, len(pptx_content['slides']) + 1))
        omitted = all_slides - matched_slides
        
        for slide_num in omitted:
            slide_type = pptx_structure['slide_types'].get(slide_num, 'unknown')
            transformations['omitted_slides'].append({
                'slide': slide_num,
                'type': slide_type,
                'preview': slide_texts[slide_num][:100] + '...' if slide_texts[slide_num] else ''
            })
        
        # Analyze structure transformation
        transformations['structure_mapping'] = {
            'pptx_chapters': len(pptx_structure.get('chapters', [])),
            'storyboard_chapters': len(storyboard_structure.get('chapters', [])),
            'chapter_names': [ch['title'] for ch in storyboard_structure.get('chapters', [])]
        }
        
        return transformations
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def aggregate_patterns(self, all_results: List[Dict]) -> Dict:
        """Aggregate patterns across all examples"""
        aggregated = {
            'total_examples': len(all_results),
            'slide_type_transformations': defaultdict(Counter),
            'common_omissions': Counter(),
            'combination_patterns': [],
            'structure_patterns': Counter(),
            'chapter_templates': []
        }
        
        for result in all_results:
            transforms = result['transformations']
            pptx_structure = result['pptx_structure']
            
            # Track which slide types get omitted
            for omitted in transforms['omitted_slides']:
                slide_type = omitted['type']
                aggregated['common_omissions'][slide_type] += 1
            
            # Track slide combinations
            for combo in transforms['combined_slides']:
                if len(combo['slides']) > 1:
                    # Get types of combined slides
                    types = [pptx_structure['slide_types'].get(s, 'unknown') for s in combo['slides']]
                    aggregated['combination_patterns'].append({
                        'types': types,
                        'count': len(combo['slides']),
                        'into': combo['into']
                    })
            
            # Track structure patterns
            struct_map = transforms['structure_mapping']
            chapter_pattern = tuple(struct_map['chapter_names'])
            aggregated['structure_patterns'][chapter_pattern] += 1
        
        # Find most common patterns
        aggregated['most_common_structure'] = aggregated['structure_patterns'].most_common(3)
        aggregated['most_omitted_types'] = aggregated['common_omissions'].most_common(5)
        
        return aggregated
    
    def _stringify_tuple_keys(self, d):
        """Recursively convert tuple keys in a dict to strings for JSON serialization."""
        if isinstance(d, dict):
            new_dict = {}
            for k, v in d.items():
                if isinstance(k, tuple):
                    key = '|'.join(str(x) for x in k)
                else:
                    key = str(k)
                new_dict[key] = self._stringify_tuple_keys(v)
            return new_dict
        elif isinstance(d, list):
            return [self._stringify_tuple_keys(x) for x in d]
        else:
            return d

    def generate_report(self, patterns: Dict) -> None:
        """Generate a readable report of findings"""
        print("\n" + "=" * 60)
        print("PATTERN ANALYSIS REPORT")
        print("=" * 60)
        
        print(f"\nAnalyzed {patterns['total_examples']} example pairs")
        
        print("\n1. MOST COMMONLY OMITTED SLIDE TYPES:")
        print("-" * 40)
        for slide_type, count in patterns['most_omitted_types']:
            percentage = (count / patterns['total_examples']) * 100
            print(f"   - {slide_type}: {count} times ({percentage:.1f}% of examples)")
        
        print("\n2. MOST COMMON CHAPTER STRUCTURES:")
        print("-" * 40)
        for structure, count in patterns['most_common_structure']:
            print(f"   {count} examples used:")
            for chapter in structure:
                print(f"      - {chapter}")
        
        print("\n3. SLIDE COMBINATION PATTERNS:")
        print("-" * 40)
        # Group combination patterns
        combo_summary = defaultdict(int)
        for pattern in patterns['combination_patterns']:
            key = f"{pattern['count']} {pattern['types'][0]} slides"
            combo_summary[key] += 1
        
        for combo, count in sorted(combo_summary.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {combo}: {count} occurrences")
        
        print("\n" + "=" * 60)
        
        # Save detailed report
        report_path = Path("pattern_analysis_report.json")
        # Convert tuple keys to strings for JSON serialization
        patterns_serializable = self._stringify_tuple_keys(patterns)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(patterns_serializable, f, indent=2, default=str)
        print(f"\nDetailed report saved to: {report_path}")


def main():
    """Run the example analyzer"""
    analyzer = ExampleAnalyzer("examples")
    patterns = analyzer.analyze_all_examples()
    
    # Save patterns for use in generation
    patterns_file = Path("learned_patterns.json")
    with open(patterns_file, 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2, default=str)
    
    print(f"\nLearned patterns saved to: {patterns_file}")
    print("\nAnalysis complete! Review the patterns to understand transformation rules.")


if __name__ == "__main__":
    main()