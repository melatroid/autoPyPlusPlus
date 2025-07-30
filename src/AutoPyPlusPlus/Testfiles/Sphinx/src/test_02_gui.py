"""
hello_return_gui.py

A simple example module that displays a success message in a Tkinter GUI.
"""

import tkinter as tk
from tkinter import messagebox

def main():
    """
    Main function of the program.

    Opens a Tkinter window, displays a success message,
    and closes the window when the button is clicked.
    """
    result = "With a gui - test successfully"  # Message to display

    # Create the main window
    root = tk.Tk()
    root.title("Result")
    root.geometry("300x150")

    # Show the message in a label
    label = tk.Label(root, text=result, font=("Arial", 12))
    label.pack(pady=20)

    # Close the window with a button
    button = tk.Button(root, text="Close", command=root.destroy)
    button.pack(pady=10)

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
