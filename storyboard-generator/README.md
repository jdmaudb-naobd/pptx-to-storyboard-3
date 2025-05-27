# Storyboard Generator

## Overview
The Storyboard Generator is a Python application designed to process slide decks and generate corresponding storyboards. Users can easily drop their slide decks into the designated input folder, and the application will handle the rest.

## Project Structure
```
storyboard-generator
├── input          # Folder for placing new slide decks
├── src            # Source code for the application
│   ├── main.py    # Main entry point of the application
│   └── utils.py   # Utility functions for processing slide decks
├── requirements.txt # List of dependencies
└── README.md      # Documentation for the project
```

## Getting Started

### Prerequisites
Make sure you have Python installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd storyboard-generator
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage
1. Place your slide deck files in the `input` folder.
2. Run the application:
   ```
   python src/main.py
   ```
3. The generated storyboard will be created based on the slide decks provided.

## Contributing
If you would like to contribute to the project, please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.