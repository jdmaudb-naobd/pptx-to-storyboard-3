"""
Run anonymized diagnostic analysis on Word documents
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Import the anonymized analyzer
from src.diagnostic_analyzer import AnonymizedDiagnosticAnalyzer

def main():
    """Run anonymized diagnostic analysis"""
    print("🔍 Anonymized Storyboard Structure Analysis")
    print("=" * 60)
    print("This will analyze structure without revealing any content")
    print()
    
    try:
        analyzer = AnonymizedDiagnosticAnalyzer()
        analyzer.analyze_all_documents("examples")
        
        print("\n✅ Analysis complete!")
        print("\nThe report shows:")
        print("- Paragraph styles used (no content)")
        print("- Table dimensions and patterns") 
        print("- Document structure patterns")
        print("- Chapter/section statistics")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        print("\nPlease ensure:")
        print("1. Your examples folder structure is correct:")
        print("   examples/output/project1/*.docx")
        print("   examples/output/project2/*.docx")
        print("   etc.")
        print("2. All .docx files are valid and not corrupted")
        
        # More detailed error info
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()