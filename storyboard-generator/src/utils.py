def read_slide_deck(file_path):
    """Reads a slide deck from the specified file path."""
    with open(file_path, 'r') as file:
        content = file.readlines()
    return content

def parse_slide_content(content):
    """Parses the content of a slide deck and returns structured data."""
    slides = []
    for line in content:
        if line.strip():  # Ignore empty lines
            slides.append(line.strip())
    return slides

def format_storyboard(slides):
    """Formats the parsed slides into a storyboard format."""
    storyboard = "\n".join(f"Slide {i + 1}: {slide}" for i, slide in enumerate(slides))
    return storyboard

def save_storyboard(output_path, storyboard):
    """Saves the generated storyboard to the specified output path."""
    with open(output_path, 'w') as file:
        file.write(storyboard)