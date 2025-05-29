"""
Script to run the example analyzer on your input/output pairs
"""

import sys
from pathlib import Path

# Add src to path if needed
sys.path.append(str(Path(__file__).parent / "src"))

from src.example_analyzer import ExampleAnalyzer

def main():
    print("PowerPoint to Storyboard Pattern Analyzer")
    print("=" * 60)
    print("\nThis tool will analyze your example input/output pairs to learn")
    print("transformation patterns for creating storyboards.\n")
    
    # Check if examples folder exists
    examples_path = Path("examples")
    if not examples_path.exists():
        print("ERROR: 'examples' folder not found!")
        print("\nPlease ensure your folder structure is:")
        print("  examples/")
        print("    ├── input/")
        print("    │   ├── project1/")
        print("    │   │   └── Module 1.pptx")
        print("    │   └── project2/")
        print("    │       └── Module 1.pptx")
        print("    └── output/")
        print("        ├── project1/")
        print("        │   └── Module 1.docx")
        print("        └── project2/")
        print("            └── Module 1.docx")
        return
    
    # Run the analyzer
    try:
        analyzer = ExampleAnalyzer("examples")
        patterns = analyzer.analyze_all_examples()
        
        if patterns:
            print("\n✓ Analysis complete!")
            print("\nKey findings have been saved to:")
            print("  - pattern_analysis_report.json (detailed report)")
            print("  - learned_patterns.json (for use in generation)")
            
            print("\n📊 Quick Summary:")
            print(f"  - Analyzed {patterns.get('total_examples', 0)} example pairs")
            print(f"  - Found {len(patterns.get('most_omitted_types', []))} commonly omitted slide types")
            print(f"  - Discovered {len(patterns.get('most_common_structure', []))} common chapter structures")
            
            print("\nNext steps:")
            print("1. Review the pattern_analysis_report.json for detailed insights")
            print("2. Use these patterns to generate new storyboards with the pattern-based generator")
        else:
            print("\n❌ No patterns found. Please check your examples folder structure.")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nPlease ensure:")
        print("1. Your examples folder has the correct structure")
        print("2. All required dependencies are installed")
        print("3. The PPTX and DOCX files are not corrupted")
        
        # More detailed error info
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()