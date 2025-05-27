"""
Setup script to initialize the medical abbreviations database
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.abbreviation_database import MedicalAbbreviationDB

def download_sample_dataset():
    """Download a sample medical abbreviations dataset"""
    import requests
    
    print("Downloading sample medical abbreviations dataset...")
    
    # Example: Download from a public dataset
    urls = {
        'clinical_abbreviations.csv': 'https://raw.githubusercontent.com/glutanimate/medical-abbreviations/master/medical_abbreviations.csv',
        # Add more dataset URLs here
    }
    
    os.makedirs('data/datasets', exist_ok=True)
    
    for filename, url in urls.items():
        output_path = f'data/datasets/{filename}'
        if not os.path.exists(output_path):
            print(f"Downloading {filename}...")
            response = requests.get(url)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded to {output_path}")

def setup_database():
    """Initialize and populate the abbreviations database"""
    print("Setting up medical abbreviations database...")
    
    # Create database
    db = MedicalAbbreviationDB()
    
    # Import existing JSON file
    if os.path.exists('data/medical_abbreviations.json'):
        print("Importing existing abbreviations...")
        import json
        with open('data/medical_abbreviations.json', 'r') as f:
            abbrevs = json.load(f)
        
        for abbr, definition in abbrevs.items():
            db.add_custom_abbreviation(abbr, definition, 'Core')
    
    # Import downloaded datasets
    csv_files = Path('data/datasets').glob('*.csv')
    for csv_file in csv_files:
        print(f"Importing {csv_file.name}...")
        # Adjust column names based on your CSV format
        db.import_csv_dataset(str(csv_file), 
                            abbr_col='abbreviation', 
                            def_col='definition')
    
    # Import UMLS if available
    umls_file = 'data/datasets/LRABR'
    if os.path.exists(umls_file):
        print("Importing UMLS abbreviations...")
        db.import_umls_file(umls_file)
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\nDatabase setup complete!")
    print(f"Total abbreviations: {stats['total_abbreviations']}")
    print(f"Categories: {stats['categories']}")
    
    # Export backup
    db.export_to_json('data/abbreviations_backup.json')
    
    db.close()

if __name__ == "__main__":
    # Download sample datasets
    download_sample_dataset()
    
    # Setup database
    setup_database()
    
    print("\nSetup complete! You can now run your PowerPoint converter with enhanced abbreviation lookup.")