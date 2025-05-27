"""
Main script to run the PowerPoint to Storyboard converter
"""

from pathlib import Path
import json
import sys
import os
from glob import glob
from src.extractor import SimpleExtractor
from src.medical_processor import MedicalContentProcessor  # Use medical processor
from src.generator import StoryboardGenerator

def convert_pptx_to_storyboard(
    pptx_path: str,
    output_path: str = None,
    template_path: str = None,
    save_json: bool = True
):
    """
    Convert a PowerPoint file to a storyboard document
    """
    pptx_path = Path(pptx_path)
    if not output_path:
        output_path = pptx_path.with_suffix('.docx')

    print(f"\nProcessing: {pptx_path.name}")
    print("=" * 60)

    # Step 1: Extract content
    print("1. Extracting content from PowerPoint...")
    extractor = SimpleExtractor(pptx_path)

    if save_json:
        json_path = pptx_path.with_suffix('.json')
        content = extractor.save_as_json(json_path)
    else:
        content = extractor.extract_all_content()

    # Step 2: Process content with medical processor
    print("\n2. Analyzing presentation structure...")
    processor = MedicalContentProcessor()
    structure = processor.identify_structure(content)
    
    print("\n3. Extracting key information...")
    abbreviations = processor.extract_abbreviations(content)
    objectives = processor.extract_objectives(content)
    references = processor.extract_references(content)

    # Display analysis results
    print(f"\n   ✓ Presentation type: Medical/Clinical")
    print(f"   ✓ Found {len(structure.get('chapters', []))} logical sections")
    print(f"   ✓ Found {len(abbreviations)} abbreviations ({sum(1 for v in abbreviations.values() if 'Not defined' in v)} undefined)")
    print(f"   ✓ Found {len(objectives)} learning objectives")
    print(f"   ✓ Found {sum(len(refs) for refs in references.values())} references")

    # Show structure with slide types
    print("\n4. Document Structure:")
    for idx, chapter in enumerate(structure.get('chapters', [])):
        slide_count = len(chapter.get('slides', []))
        print(f"\n   {idx + 1}. {chapter['title']} ({slide_count} slides)")
        
        # Show first few slides with their types
        for slide_num in chapter.get('slides', [])[:3]:
            slide_type = structure['slide_types'].get(slide_num, 'content')
            print(f"      - Slide {slide_num}: {slide_type}")
        
        if len(chapter.get('slides', [])) > 3:
            print(f"      ... and {len(chapter.get('slides', [])) - 3} more slides")
        
        # Show subchapters
        for sub_idx, subchapter in enumerate(chapter.get('subchapters', [])):
            print(f"      {idx + 1}.{sub_idx + 1} {subchapter['title']} ({len(subchapter.get('slides', []))} slides)")

    # Step 3: Generate document
    print("\n5. Generating storyboard document...")
    generator = StoryboardGenerator(template_path)

    # Add sections
    generator.create_title_page(pptx_path.stem)
    generator.create_contents_table(structure)
    generator.create_abbreviations_table(abbreviations)
    generator.create_objectives_section(objectives)

    # Track which slides have been added
    added_slides = set()

    # Add content for each slide in structure
    for chapter in structure.get('chapters', []):
        current_chapter = chapter['title']
        
        # Add chapter heading if it has many slides
        if len(chapter.get('slides', [])) > 1:
            generator.doc.add_heading(current_chapter, 2)
        
        # Add chapter slides
        for slide_num in chapter.get('slides', []):
            if slide_num <= len(content['slides']):
                slide_data = content['slides'][slide_num - 1]
                slide_refs = references.get(slide_num, [])
                generator.create_content_table(slide_data, current_chapter, "", slide_refs, abbreviations)
                added_slides.add(slide_num)
        
        # Add subchapter slides
        for subchapter in chapter.get('subchapters', []):
            current_subchapter = subchapter['title']
            
            # Add subchapter heading
            generator.doc.add_heading(f"{current_subchapter}", 3)
            
            for slide_num in subchapter.get('slides', []):
                if slide_num <= len(content['slides']) and slide_num not in added_slides:
                    slide_data = content['slides'][slide_num - 1]
                    slide_refs = references.get(slide_num, [])
                    generator.create_content_table(slide_data, current_chapter, current_subchapter, slide_refs, abbreviations)
                    added_slides.add(slide_num)

    # Save document
    generator.save(output_path)
    print(f"\n✓ Complete! Storyboard saved to: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"

    # Ensure input and output folders exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    if len(sys.argv) < 2:
        # No arguments: process all pptx files in input/
        pptx_files = glob(os.path.join(input_dir, "*.pptx"))
        if not pptx_files:
            print(f"No PPTX files found in '{input_dir}' folder.")
            print("\nTo use this converter:")
            print("1. Place your PowerPoint files in the 'input' folder")
            print("2. Run this script again")
            print("\nThe storyboards will be created in the 'output' folder")
        else:
            print(f"Medical Presentation to Storyboard Converter")
            print(f"Found {len(pptx_files)} PowerPoint file(s) to process")
            
            for pptx_path in pptx_files:
                filename = os.path.splitext(os.path.basename(pptx_path))[0]
                output_path = os.path.join(output_dir, f"{filename}_storyboard.docx")
                convert_pptx_to_storyboard(pptx_path, output_path)
            
            print(f"\n✓ All files processed! Check the '{output_dir}' folder for results.")
    else:
        pptx_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        template_path = sys.argv[3] if len(sys.argv) > 3 else None

        convert_pptx_to_storyboard(pptx_path, output_path, template_path)