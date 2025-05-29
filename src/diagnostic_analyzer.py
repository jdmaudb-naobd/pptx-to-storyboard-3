"""
Anonymized diagnostic analyzer to understand Word document structure
"""

import os
from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
import json
from typing import Dict, List
from collections import defaultdict, Counter
from .utils import is_abbreviation_table


class AnonymizedDiagnosticAnalyzer:
    """Diagnose Word document structure without revealing content"""
    
    def __init__(self):
        self.findings = []
        self.style_usage = Counter()
        self.table_patterns = Counter()
        self.document_patterns = []
        
    def analyze_docx_structure(self, docx_path: Path, project_num: int, doc_num: int) -> Dict:
        """Analyze the structure of a Word document anonymously"""
        doc = Document(str(docx_path))
        
        analysis = {
            'project': f"Project_{project_num}",
            'document': f"Doc_{doc_num}",
            'element_sequence': [],  # Just types, no content
            'style_counts': Counter(),
            'table_structures': [],
            'chapter_count': 0,
            'total_elements': 0
        }
        
        # Analyze each element in order
        for idx, element in enumerate(doc.element.body):
            if element.tag.endswith('p'):
                # It's a paragraph
                para = Paragraph(element, doc)
                text = para.text.strip()
                style = para.style.name if para.style else "No Style"
                
                if text:  # Only process non-empty paragraphs
                    analysis['style_counts'][style] += 1
                    self.style_usage[style] += 1
                    
                    # Record element type and characteristics without content
                    element_info = {
                        'type': 'paragraph',
                        'style': style,
                        'word_count': len(text.split()),
                        'char_count': len(text),
                        'has_numbers': any(c.isdigit() for c in text),
                        'has_bullet': text.startswith(('•', '-', '*', '▪', '►')),
                        'ends_with_punctuation': text[-1] in '.!?:' if text else False
                    }
                    
                    # Check if it might be a chapter (anonymized)
                    if self._might_be_chapter_anonymous(element_info):
                        analysis['chapter_count'] += 1
                        element_info['possible_chapter'] = True
                    
                    analysis['element_sequence'].append(element_info)
                    
            elif element.tag.endswith('tbl'):
                # It's a table
                table = Table(element, doc)
                
                # Analyze table structure anonymously
                table_info = self._analyze_table_anonymous(table)
                analysis['element_sequence'].append(table_info)
                analysis['table_structures'].append(table_info)
                
                # Track table patterns
                pattern = f"{table_info['rows']}x{table_info['cols']}"
                self.table_patterns[pattern] += 1
        
        analysis['total_elements'] = len(analysis['element_sequence'])
        
        return analysis
    
    def _might_be_chapter_anonymous(self, element_info: Dict) -> bool:
        """Determine if element might be a chapter based on structure only"""
        # Short text with certain styles often indicates chapters
        if element_info['word_count'] < 10 and element_info['style'] != 'Normal':
            return True
        
        # Short text without ending punctuation might be a heading
        if element_info['word_count'] < 8 and not element_info['ends_with_punctuation']:
            return True
            
        return False
    
    def _analyze_table_anonymous(self, table: Table) -> Dict:
        """Analyze table structure without revealing content"""
        if is_abbreviation_table(table):
            return {
                'type': 'abbreviation_table',
                'rows': len(table.rows),
                'cols': len(table.columns)
            }

        # Existing logic for other table types
        row_count = len(table.rows)
        col_count = len(table.columns)
        table_type = "unknown"

        if row_count > 3 and col_count > 2:
            table_type = "possible_data_table"

        return {
            'type': 'table',
            'rows': row_count,
            'cols': col_count,
            'probable_type': table_type,
            'has_merged_cells': self._has_merged_cells(table)
        }
    
    def _has_merged_cells(self, table: Table) -> bool:
        """Check if table has merged cells"""
        try:
            cell_count = sum(len(row.cells) for row in table.rows)
            expected_count = len(table.rows) * len(table.columns)
            return cell_count != expected_count
        except:
            return False
    
    def analyze_all_documents(self, examples_dir: str = "examples") -> None:
        """Analyze ALL documents across ALL projects"""
        output_dir = Path(examples_dir) / "output"
        
        if not output_dir.exists():
            print(f"Error: Output directory not found at {output_dir}")
            return
        
        print("🔍 Analyzing ALL storyboard documents (anonymized)")
        print("=" * 60)
        
        all_projects = [d for d in output_dir.iterdir() if d.is_dir()]
        total_docs = 0
        
        # Analyze all documents
        for proj_idx, project_dir in enumerate(all_projects, 1):
            docx_files = list(project_dir.glob("*.docx"))
            
            for doc_idx, docx_file in enumerate(docx_files, 1):
                print(f"   Analyzing Project_{proj_idx}/Doc_{doc_idx}...")
                analysis = self.analyze_docx_structure(docx_file, proj_idx, doc_idx)
                self.document_patterns.append(analysis)
                total_docs += 1
        
        print(f"\n✅ Analyzed {total_docs} documents across {len(all_projects)} projects")
        
        # Generate anonymized report
        self._generate_anonymized_report(total_docs)
    
    def _generate_anonymized_report(self, total_docs: int) -> None:
        """Generate an anonymized structural report"""
        report = {
            'summary': {
                'total_documents': total_docs,
                'total_projects': len(set(d['project'] for d in self.document_patterns))
            },
            'paragraph_styles': {},
            'table_patterns': {},
            'document_structures': [],
            'common_patterns': {}
        }
        
        # Paragraph styles usage
        print("\n📝 PARAGRAPH STYLES FOUND (anonymized):")
        print("-" * 40)
        for style, count in self.style_usage.most_common():
            percentage = (count / sum(self.style_usage.values())) * 100
            print(f"   {style}: {count} occurrences ({percentage:.1f}%)")
            report['paragraph_styles'][style] = {
                'count': count,
                'percentage': percentage
            }
        
        # Table patterns
        print("\n📊 TABLE PATTERNS FOUND:")
        print("-" * 40)
        for pattern, count in self.table_patterns.most_common():
            print(f"   {pattern} tables: {count} occurrences")
            report['table_patterns'][pattern] = count
        
        # Document structure patterns
        print("\n📄 DOCUMENT STRUCTURE PATTERNS:")
        print("-" * 40)
        
        # Analyze common element sequences
        structure_patterns = Counter()
        for doc in self.document_patterns:
            # Create a simplified structure signature
            structure = []
            for elem in doc['element_sequence']:
                if elem['type'] == 'paragraph':
                    if elem.get('possible_chapter'):
                        structure.append('CHAPTER')
                    elif elem['word_count'] < 20:
                        structure.append('SHORT_PARA')
                    else:
                        structure.append('PARA')
                elif elem['type'] == 'table':
                    structure.append(f"TABLE_{elem['probable_type']}")
            
            # Look at beginning pattern
            if len(structure) > 5:
                start_pattern = tuple(structure[:5])
                structure_patterns[start_pattern] += 1
        
        print("   Most common document beginnings:")
        for pattern, count in structure_patterns.most_common(5):
            print(f"   {' -> '.join(pattern)}: {count} docs")
        
        # Chapter statistics
        chapter_counts = [d['chapter_count'] for d in self.document_patterns]
        avg_chapters = sum(chapter_counts) / len(chapter_counts) if chapter_counts else 0
        
        print(f"\n📚 CHAPTER STATISTICS:")
        print(f"   Average chapters per document: {avg_chapters:.1f}")
        print(f"   Min chapters: {min(chapter_counts) if chapter_counts else 0}")
        print(f"   Max chapters: {max(chapter_counts) if chapter_counts else 0}")
        
        # Element type distribution
        print(f"\n📋 ELEMENT TYPE DISTRIBUTION:")
        element_counts = Counter()
        for doc in self.document_patterns:
            for elem in doc['element_sequence']:
                element_counts[elem['type']] += 1
        
        total_elements = sum(element_counts.values())
        for elem_type, count in element_counts.items():
            percentage = (count / total_elements) * 100
            print(f"   {elem_type}: {count} ({percentage:.1f}%)")
        
        # Save detailed report
        with open("anonymized_structure_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: anonymized_structure_report.json")