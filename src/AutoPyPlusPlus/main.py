def main():
    import tkinter as tk
    from .gui import AutoPyPlusPlusGUI

    root = tk.Tk()
    app = AutoPyPlusPlusGUI(root)
    root.mainloop()
