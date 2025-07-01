# hello_return_gui.py

import tkinter as tk
from tkinter import messagebox

def main():
    result = "With a gui - test successfully"

    # Erstelle das Hauptfenster
    root = tk.Tk()
    root.title("Ergebnis")
    root.geometry("300x150")

    # Zeige den Text in einem Label an
    label = tk.Label(root, text=result, font=("Arial", 12))
    label.pack(pady=20)

    # Schließe das Fenster mit einem Button
    button = tk.Button(root, text="Schließen", command=root.destroy)
    button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
