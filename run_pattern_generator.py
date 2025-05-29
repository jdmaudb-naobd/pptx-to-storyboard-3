"""
Run the pattern-based storyboard generator
"""

import sys
import os
from pathlib import Path
from glob import glob

# Add src to path
sys.path.append(str(Path(__file__).parent))

# First, save the pattern-based generator to src
pattern_generator_path = Path("src/pattern_generator.py")
if not pattern_generator_path.exists():
    print("📝 Creating pattern generator module...")
    # Copy the pattern generator code to src/pattern_generator.py
    # (In practice, you would copy the artifact content to this file)

from src.pattern_generator import PatternBasedGenerator

def process_single_file(generator: PatternBasedGenerator, pptx_path: str, output_dir: str):
    """Process a single PowerPoint file"""
    input_path = Path(pptx_path)
    output_name = f"{input_path.stem}_storyboard.docx"
    output_path = Path(output_dir) / output_name
    
    try:
        generator.generate_storyboard(str(input_path), str(output_path))
        print(f"✅ Generated: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error processing {input_path.name}: {str(e)}")
        return False

def main():
    print("🚀 Pattern-Based Storyboard Generator")
    print("=" * 60)
    print("\nThis tool uses learned patterns to create eLearning storyboards")
    print("from PowerPoint presentations.")
    
    # Check for learned patterns
    if not Path("learned_patterns.json").exists():
        print("\n❌ Error: learned_patterns.json not found!")
        print("Please run the pattern analyzer first.")
        return
    
    # Initialize generator
    generator = PatternBasedGenerator("learned_patterns.json")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Process specific file
        pptx_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not Path(pptx_path).exists():
            print(f"❌ Error: File not found: {pptx_path}")
            return
        
        print(f"\nProcessing: {pptx_path}")
        generator.generate_storyboard(pptx_path, output_path)
        
    else:
        # Process all files in input folder
        input_dir = "input"
        output_dir = "output"
        
        # Create directories if needed
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Find PowerPoint files
        pptx_files = glob(os.path.join(input_dir, "*.pptx"))
        
        if not pptx_files:
            print(f"\n📁 No PowerPoint files found in '{input_dir}' folder")
            print("\nUsage options:")
            print("1. Place .pptx files in the 'input' folder and run again")
            print("2. Run with arguments: python run_pattern_generator.py input.pptx [output.docx]")
            return
        
        print(f"\n📁 Found {len(pptx_files)} PowerPoint files to process")
        print(f"📂 Output directory: {output_dir}")
        print()
        
        # Process each file
        success_count = 0
        for pptx_path in pptx_files:
            if process_single_file(generator, pptx_path, output_dir):
                success_count += 1
        
        print(f"\n📊 Summary: {success_count}/{len(pptx_files)} files processed successfully")
        print(f"📁 Check the '{output_dir}' folder for results")

if __name__ == "__main__":
    main()