import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess

def run_program(input_file, output_dir):
    """Run the storyboard generator program."""
    try:
        command = f"python run_pattern_generator.py --input {input_file} --output {output_dir}"
        subprocess.run(command, shell=True, check=True)
        messagebox.showinfo("Success", "Storyboard generated successfully!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to generate storyboard: {e}")

def select_input_file():
    """Open file dialog to select input file."""
    file_path = filedialog.askopenfilename(
        title="Select PowerPoint File",
        filetypes=[("PowerPoint Files", "*.pptx")]
    )
    input_file_var.set(file_path)

def select_output_dir():
    """Open file dialog to select output directory."""
    dir_path = filedialog.askdirectory(title="Select Output Directory")
    output_dir_var.set(dir_path)

def run():
    """Run the program with selected input and output."""
    input_file = input_file_var.get()
    output_dir = output_dir_var.get()

    if not input_file or not output_dir:
        messagebox.showwarning("Warning", "Please select both input file and output directory.")
        return

    run_program(input_file, output_dir)

# Create the main GUI window
root = tk.Tk()
root.title("Storyboard Generator")

# Input file selection
input_file_var = tk.StringVar()
output_dir_var = tk.StringVar()

tk.Label(root, text="Input PowerPoint File:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
tk.Entry(root, textvariable=input_file_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=select_input_file).grid(row=0, column=2, padx=10, pady=10)

# Output directory selection
tk.Label(root, text="Output Directory:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
tk.Entry(root, textvariable=output_dir_var, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=select_output_dir).grid(row=1, column=2, padx=10, pady=10)

# Run button
tk.Button(root, text="Generate Storyboard", command=run).grid(row=2, column=0, columnspan=3, pady=20)

# Start the GUI event loop
root.mainloop()
