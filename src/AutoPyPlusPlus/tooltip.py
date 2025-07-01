import tkinter as tk

class CreateToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.show_id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        if self.show_id is None:
            self.show_id = self.widget.after(500, self.show_tooltip)

    def show_tooltip(self):
        if self.show_id is None:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 10))
        label.pack()
        self.show_id = None

    def hide_tooltip(self, event=None):
        if self.show_id:
            self.widget.after_cancel(self.show_id)
            self.show_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
