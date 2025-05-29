"""
Re-run pattern analysis with the fixed parser
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.example_analyzer import ExampleAnalyzer

def main():
    print("🔄 Re-running Pattern Analysis with Fixed Parser")
    print("=" * 60)
    print("\nThis will use the corrected document parser that recognizes:")
    print("  - Heading 1 → Chapters")
    print("  - AX Subhead → Subchapters")
    print("  - 11x2 tables → Abbreviations")
    print("  - Nx3/Nx4 tables → Content segments")
    print()
    
    try:
        # Run the analyzer with the fixed parser
        analyzer = ExampleAnalyzer("examples")
        patterns = analyzer.analyze_all_examples()
        
        if patterns and patterns.get('total_examples', 0) > 0:
            print("\n✅ Analysis complete with fixed parser!")
            print("\n📊 Updated Summary:")
            print(f"  - Analyzed {patterns.get('total_examples', 0)} example pairs")
            
            # Show updated omission patterns
            print("\n📑 Most Commonly Omitted Slide Types (Updated):")
            for slide_type, count in patterns.get('most_omitted_types', [])[:5]:
                percentage = (count / patterns['total_examples']) * 100
                print(f"  - {slide_type}: {count} times ({percentage:.1f}% of examples)")
            
            # Show structure patterns
            print("\n🏗️ Document Structure Patterns (Updated):")
            for structure, count in patterns.get('most_common_structure', [])[:3]:
                if structure and structure != '()':  # Should now have actual chapters
                    print(f"\n  Pattern used in {count} documents:")
                    for chapter in structure[:5]:  # Show first 5 chapters
                        print(f"    - {chapter}")
                    if len(structure) > 5:
                        print(f"    ... and {len(structure) - 5} more chapters")
            
            print("\n📁 Updated files:")
            print("  - pattern_analysis_report.json (detailed findings)")
            print("  - learned_patterns.json (for pattern-based generation)")
            
        else:
            print("\n⚠️ No patterns found. Please check:")
            print("  1. Document styles match: Heading 1, AX Subhead")
            print("  2. Table formats are being detected correctly")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()