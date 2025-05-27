"""
Main script to run the PowerPoint to Storyboard converter
"""

from pathlib import Path
import json
import sys
import os
from glob import glob
from src.extractor import SimpleExtractor
from src.processor import ContentProcessor
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

    print(f"Processing: {pptx_path}")

    # Step 1: Extract content
    print("1. Extracting content...")
    extractor = SimpleExtractor(pptx_path)

    if save_json:
        json_path = pptx_path.with_suffix('.json')
        content = extractor.save_as_json(json_path)
    else:
        content = extractor.extract_all_content()

    # Step 2: Process content
    print("2. Processing content...")
    processor = ContentProcessor()
    structure = processor.identify_structure(content)
    abbreviations = processor.extract_abbreviations(content)
    objectives = processor.extract_objectives(content)
    references = processor.extract_references(content)

    print(f"   Found {len(structure.get('chapters', []))} chapters")
    print(f"   Found {len(abbreviations)} abbreviations")
    print(f"   Found {len(objectives)} objectives")
    print(f"   Found {len(references)} references")

    # Debug: Print total slides and breakdown by chapter and subchapter
    print(f"Total slides in content: {len(content['slides'])}")
    for chapter in structure.get('chapters', []):
        print(f"Chapter: {chapter['title']}, slides: {chapter.get('slides', [])}")
        for subchapter in chapter.get('subchapters', []):
            print(f"  Subchapter: {subchapter['title']}, slides: {subchapter.get('slides', [])}")

    # Step 3: Generate document
    print("3. Generating storyboard document...")
    generator = StoryboardGenerator(template_path)

    # Add sections
    generator.create_title_page(pptx_path.stem)
    generator.create_contents_table(structure)
    generator.create_abbreviations_table(abbreviations)
    generator.create_objectives_section(objectives)

    # Add content for each slide
    for chapter in structure.get('chapters', []):
        current_chapter = chapter['title']
        # Add chapter slides
        for slide_num in chapter.get('slides', []):
            slide_data = content['slides'][slide_num - 1]
            generator.create_content_table(slide_data, current_chapter, "")
        # Add subchapter slides
        for subchapter in chapter.get('subchapters', []):
            current_subchapter = subchapter['title']
            for slide_num in subchapter.get('slides', []):
                slide_data = content['slides'][slide_num - 1]
                generator.create_content_table(slide_data, current_chapter, current_subchapter)

    # Add this after your chapter/subchapter processing if you want to ensure all slides are included
    for idx, slide_data in enumerate(content['slides']):
        generator.create_content_table(slide_data, "Unassigned", "")

    # Save document
    generator.save(output_path)
    print(f"\nComplete! Output saved to: {output_path}")

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
            print("Drop your .pptx files into the 'input' folder and run this script again.")
        else:
            for pptx_path in pptx_files:
                filename = os.path.splitext(os.path.basename(pptx_path))[0]
                output_path = os.path.join(output_dir, f"{filename}.docx")
                print(f"\nProcessing {pptx_path} -> {output_path}")
                convert_pptx_to_storyboard(pptx_path, output_path)
    else:
        pptx_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        template_path = sys.argv[3] if len(sys.argv) > 3 else None

        convert_pptx_to_storyboard(pptx_path, output_path, template_path)