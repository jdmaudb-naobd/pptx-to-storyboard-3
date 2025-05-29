"""
Setup script for pattern-based generator
"""

from pathlib import Path
import shutil

print("🔧 Setting up Pattern-Based Storyboard Generator")
print("=" * 50)

# Check if src/pattern_generator.py exists
pattern_gen_path = Path("src/pattern_generator.py")

if not pattern_gen_path.exists():
    print("\n⚠️  Pattern generator not found in src/")
    print("Please save the PatternBasedGenerator code to:")
    print("  src/pattern_generator.py")
    print("\nYou can copy it from the artifact shown in the conversation")
else:
    print("✅ Pattern generator found")

# Check for learned patterns
if Path("learned_patterns.json").exists():
    print("✅ Learned patterns found")
else:
    print("❌ learned_patterns.json not found")
    print("   Run: python run_simple_analyzer.py")

# Check for required modules
required_files = [
    "src/__init__.py",
    "src/extractor.py", 
    "src/medical_processor.py",
    "src/generator.py"
]

missing = [f for f in required_files if not Path(f).exists()]
if missing:
    print(f"\n⚠️  Missing required files:")
    for f in missing:
        print(f"   - {f}")
else:
    print("✅ All required modules found")

# Create example structure
print("\n📁 Creating folder structure...")
Path("input").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)

print("\n✅ Setup complete!")
print("\nTo use the pattern-based generator:")
print("1. Copy PatternBasedGenerator code to src/pattern_generator.py")
print("2. Place PowerPoint files in the 'input' folder")
print("3. Run: python run_pattern_generator.py")
print("\nOr process a single file:")
print("   python run_pattern_generator.py presentation.pptx output.docx")