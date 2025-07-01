# hotkeys.py
def register_hotkeys(root, callbacks: dict):
    """
    Registriert Hotkeys in einem Tkinter-Fenster (root).

    :param root: Tkinter-Root- oder Toplevel-Fenster
    :param callbacks: dict { "<Hotkey>": callbackFunktion }
    """
    for hotkey, callback in callbacks.items():
        root.bind(hotkey, lambda event, cb=callback: cb())