"""
Script to add custom abbreviations to the database
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.abbreviation_database import MedicalAbbreviationDB

def add_abbreviations_interactive():
    """Interactive script to add abbreviations"""
    db = MedicalAbbreviationDB()
    
    print("Medical Abbreviation Manager")
    print("=" * 40)
    
    while True:
        print("\n1. Add new abbreviation")
        print("2. Look up abbreviation")
        print("3. Show statistics")
        print("4. Export database")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            abbr = input("Abbreviation: ").strip().upper()
            definition = input("Definition: ").strip()
            category = input("Category (or press Enter for 'Custom'): ").strip() or 'Custom'
            
            db.add_custom_abbreviation(abbr, definition, category)
            print(f"✓ Added {abbr} = {definition}")
        
        elif choice == '2':
            abbr = input("Enter abbreviation to look up: ").strip()
            result = db.lookup(abbr)
            
            if result['found']:
                print(f"\n{abbr}:")
                for i, defn in enumerate(result['definitions'], 1):
                    print(f"  {i}. {defn}")
                print(f"  Category: {result['category']}")
            else:
                print(f"❌ {abbr} not found in database")
        
        elif choice == '3':
            stats = db.get_statistics()
            print(f"\nDatabase Statistics:")
            print(f"Total abbreviations: {stats['total_abbreviations']}")
            print(f"Categories:")
            for cat, count in stats['categories'].items():
                print(f"  - {cat}: {count}")
        
        elif choice == '4':
            filename = input("Export filename (or press Enter for 'export.json'): ").strip() or 'export.json'
            db.export_to_json(f'data/{filename}')
        
        elif choice == '5':
            break
    
    db.close()
    print("\nGoodbye!")

if __name__ == "__main__":
    add_abbreviations_interactive()