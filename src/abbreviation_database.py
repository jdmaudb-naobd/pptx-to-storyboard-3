"""
Medical Abbreviation Database Handler
Manages large-scale medical abbreviation lookups
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional, List, Set
import csv
import pickle

class MedicalAbbreviationDB:
    def __init__(self, db_path: str = "data/medical_abbr.db"):
        """Initialize the abbreviation database"""
        self.db_path = db_path
        self.conn = None
        self.cache = {}  # In-memory cache for frequent lookups
        self.init_database()
    
    def init_database(self):
        """Create database if it doesn't exist"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abbreviations (
                abbreviation TEXT PRIMARY KEY,
                definitions TEXT,
                category TEXT,
                source TEXT,
                confidence REAL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_abbr 
            ON abbreviations(abbreviation)
        ''')
        
        self.conn.commit()
    
    def import_umls_file(self, umls_file_path: str):
        """Import UMLS LRABR file into database"""
        print("Importing UMLS abbreviations...")
        cursor = self.conn.cursor()
        
        with open(umls_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # UMLS format: EUI|ABR|TYPE|EUI2|STR
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    abbr = parts[1]
                    full_form = parts[4]
                    
                    # Check if abbreviation already exists
                    cursor.execute(
                        "SELECT definitions FROM abbreviations WHERE abbreviation = ?",
                        (abbr,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        # Append to existing definitions
                        existing_defs = json.loads(result[0])
                        if full_form not in existing_defs:
                            existing_defs.append(full_form)
                            cursor.execute(
                                "UPDATE abbreviations SET definitions = ? WHERE abbreviation = ?",
                                (json.dumps(existing_defs), abbr)
                            )
                    else:
                        # Insert new abbreviation
                        cursor.execute(
                            "INSERT INTO abbreviations (abbreviation, definitions, source) VALUES (?, ?, ?)",
                            (abbr, json.dumps([full_form]), 'UMLS')
                        )
        
        self.conn.commit()
        print(f"Imported abbreviations successfully")
    
    def import_csv_dataset(self, csv_path: str, abbr_col: str = 'abbreviation', 
                          def_col: str = 'definition', category_col: str = None):
        """Import abbreviations from CSV file"""
        print(f"Importing abbreviations from {csv_path}...")
        cursor = self.conn.cursor()
        imported = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                abbr = row.get(abbr_col, '').strip().upper()
                definition = row.get(def_col, '').strip()
                category = row.get(category_col, 'General') if category_col else 'General'
                
                if abbr and definition:
                    cursor.execute(
                        "SELECT definitions FROM abbreviations WHERE abbreviation = ?",
                        (abbr,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        existing_defs = json.loads(result[0])
                        if definition not in existing_defs:
                            existing_defs.append(definition)
                            cursor.execute(
                                "UPDATE abbreviations SET definitions = ?, category = ? WHERE abbreviation = ?",
                                (json.dumps(existing_defs), category, abbr)
                            )
                    else:
                        cursor.execute(
                            "INSERT INTO abbreviations (abbreviation, definitions, category, source) VALUES (?, ?, ?, ?)",
                            (abbr, json.dumps([definition]), category, 'CSV')
                        )
                        imported += 1
        
        self.conn.commit()
        print(f"Imported {imported} new abbreviations")
    
    def lookup(self, abbreviation: str) -> Dict[str, any]:
        """Look up an abbreviation in the database"""
        abbr = abbreviation.upper()
        
        # Check cache first
        if abbr in self.cache:
            return self.cache[abbr]
        
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT definitions, category, confidence FROM abbreviations WHERE abbreviation = ?",
            (abbr,)
        )
        result = cursor.fetchone()
        
        if result:
            definitions = json.loads(result[0])
            response = {
                'abbreviation': abbr,
                'definitions': definitions,
                'category': result[1],
                'confidence': result[2] or 1.0,
                'found': True
            }
            
            # Cache the result
            self.cache[abbr] = response
            return response
        
        return {
            'abbreviation': abbr,
            'definitions': [],
            'found': False
        }
    
    def bulk_lookup(self, abbreviations: List[str]) -> Dict[str, Dict]:
        """Look up multiple abbreviations efficiently"""
        results = {}
        uncached = []
        
        # Check cache first
        for abbr in abbreviations:
            abbr_upper = abbr.upper()
            if abbr_upper in self.cache:
                results[abbr] = self.cache[abbr_upper]
            else:
                uncached.append(abbr_upper)
        
        # Bulk query for uncached items
        if uncached:
            cursor = self.conn.cursor()
            placeholders = ','.join('?' * len(uncached))
            cursor.execute(
                f"SELECT abbreviation, definitions, category, confidence FROM abbreviations WHERE abbreviation IN ({placeholders})",
                uncached
            )
            
            for row in cursor.fetchall():
                abbr = row[0]
                result = {
                    'abbreviation': abbr,
                    'definitions': json.loads(row[1]),
                    'category': row[2],
                    'confidence': row[3] or 1.0,
                    'found': True
                }
                self.cache[abbr] = result
                # Find original case
                for orig_abbr in abbreviations:
                    if orig_abbr.upper() == abbr:
                        results[orig_abbr] = result
                        break
        
        # Add not found entries
        for abbr in abbreviations:
            if abbr not in results:
                results[abbr] = {
                    'abbreviation': abbr,
                    'definitions': [],
                    'found': False
                }
        
        return results
    
    def add_custom_abbreviation(self, abbr: str, definition: str, category: str = 'Custom'):
        """Add a custom abbreviation to the database"""
        cursor = self.conn.cursor()
        abbr = abbr.upper()
        
        cursor.execute(
            "SELECT definitions FROM abbreviations WHERE abbreviation = ?",
            (abbr,)
        )
        result = cursor.fetchone()
        
        if result:
            definitions = json.loads(result[0])
            if definition not in definitions:
                definitions.append(definition)
                cursor.execute(
                    "UPDATE abbreviations SET definitions = ? WHERE abbreviation = ?",
                    (json.dumps(definitions), abbr)
                )
        else:
            cursor.execute(
                "INSERT INTO abbreviations (abbreviation, definitions, category, source) VALUES (?, ?, ?, ?)",
                (abbr, json.dumps([definition]), category, 'Custom')
            )
        
        self.conn.commit()
        
        # Update cache
        if abbr in self.cache:
            del self.cache[abbr]
    
    def export_to_json(self, output_path: str):
        """Export database to JSON for backup or sharing"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM abbreviations")
        
        abbreviations = {}
        for row in cursor.fetchall():
            abbr = row[0]
            definitions = json.loads(row[1])
            abbreviations[abbr] = {
                'definitions': definitions,
                'category': row[2],
                'source': row[3],
                'confidence': row[4]
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(abbreviations, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(abbreviations)} abbreviations to {output_path}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM abbreviations")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT category, COUNT(*) FROM abbreviations GROUP BY category")
        categories = dict(cursor.fetchall())
        
        return {
            'total_abbreviations': total,
            'categories': categories,
            'cache_size': len(self.cache)
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()