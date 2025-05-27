"""
Simple PowerPoint content extractor
No complex dependencies!
"""

from pptx import Presentation
import json
from pathlib import Path

class SimpleExtractor:
    def __init__(self, pptx_path):
        self.pptx_path = Path(pptx_path)
        self.presentation = Presentation(str(pptx_path))
        
    def extract_all_content(self):
        """Extract all content from PowerPoint"""
        content = {
            "filename": self.pptx_path.name,
            "slide_count": len(self.presentation.slides),
            "slides": []
        }
        
        for idx, slide in enumerate(self.presentation.slides):
            slide_content = {
                "slide_number": idx + 1,
                "texts": [],
                "shapes": []
            }
            
            # Extract text from each shape
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text_item = {
                        "text": shape.text,
                        "is_title": shape == slide.shapes.title if hasattr(slide.shapes, 'title') else False
                    }
                    slide_content["texts"].append(text_item)
                
                # Note if shape has image
                if hasattr(shape, "image"):
                    slide_content["shapes"].append({
                        "type": "image",
                        "name": shape.name
                    })
            
            content["slides"].append(slide_content)
        
        return content
    
    def save_as_json(self, output_path):
        """Save extracted content as JSON for inspection"""
        content = self.extract_all_content()
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        print(f"Content saved to {output_path}")
        return content