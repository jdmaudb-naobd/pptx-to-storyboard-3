import os
import sys
from utils import process_slide_deck, generate_storyboard

def main():
    input_folder = 'input'
    
    if not os.path.exists(input_folder):
        print(f"Input folder '{input_folder}' does not exist.")
        sys.exit(1)

    slide_decks = [f for f in os.listdir(input_folder) if f.endswith('.pptx') or f.endswith('.pdf')]
    
    if not slide_decks:
        print("No slide decks found in the input folder.")
        sys.exit(1)

    for slide_deck in slide_decks:
        slide_deck_path = os.path.join(input_folder, slide_deck)
        print(f"Processing slide deck: {slide_deck}")
        content = process_slide_deck(slide_deck_path)
        storyboard = generate_storyboard(content)
        print(f"Generated storyboard for {slide_deck}:\n{storyboard}")

if __name__ == "__main__":
    main()