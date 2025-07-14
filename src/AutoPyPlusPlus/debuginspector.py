import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import os
import re
from typing import List
import threading
from .project import Project
from .config import save_config

ERROR_RECOMMENDATIONS = {
    "permission denied": "1.) Restart System 2.) Check the file or folder permissions. Make sure the user has sufficient rights.",
    "not found": "1.) File really exists? 2.) Verify that the file or resource exists and that the path is correct.",
    "failed": "Review the previous outputs to identify the cause of the failure.",
    "exit code": "Check the meaning of the exit code in the documentation or logic.",
    "monkeypatch": "Check the usage of pytest's monkeypatch fixture. Did you import it? Is the scope correct?",
    "capsys": "Check if 'capsys' fixture is passed correctly to your test function.",
    "fixture": "Is your fixture correctly declared? Is the name matching?",
    "assert ": "Check what is being asserted and compare expected/actual values.",
    "not defined": "Did you import the module/class/function? Check for typos or circular imports.",
}

def debuginspector(master: tk.Tk, logfile: str, selected: List[Project], style: ttk.Style, config: dict) -> None:
    # Fenster und Farben
    WINDOW_TITLE = "Log Analyzer"
    WINDOW_SIZE = "1200x700"
    MIN_WINDOW_SIZE = "400x300"
    KEYWORD_PATTERNS = {
        # Allgemein
        "warning": (r"(?i)\bwarning\b", "#FFAA00"),
        "info": (r"(?i)\binfo\b", "#55AAFF"),
        "debug": (r"(?i)\bdebug\b", "#00FFAA"),
        "permission_denied": (r"(?i)permission denied", "#FF5555"),
        "success": (r"(?i)success", "#55FF55"),
        "successfully": (r"(?i)successfully", "#55FF55"),
        "not_found": (r"(?i)not found", "#FF5555"),
        "true": (r"(?i)\btrue\b", "#00FF00"),
        "false": (r"(?i)\bfalse\b", "#FF0000"),
        "failed": (r"(?i)failed", "#FF5555"),
        "end_0_errors": (r"(?i)end: 0 errors", "#55FF55"),
        "starting_compilation": (r"(?i)starting compilation", "#FFAA00"),
        # Pytest-spezifisch
        "pytest_fail": (r"(?i)\bFAILED\b|\bFAILURES\b", "#FF2222"),
        "pytest_pass": (r"(?i)\bPASSED\b|\bcollected \d+ items\b", "#55FF99"),
        "pytest_xfail": (r"(?i)\bXFAIL\b|\bXPASS\b", "#999999"),
        "pytest_error": (r"(?i)\bERROR\b", "#FF2222"),
        "pytest_trace": (r"(?i)>\s+assert\b|\s+E\s+", "#AA00FF"),
        "pytest_monkey": (r"\bmonkeypatch\b", "#00DDFF"),
        "pytest_capsys": (r"\bcapsys\b", "#00DDFF"),
        "pytest_fixture": (r"\bfixture\b", "#FF00AA"),
        "pytest_collect": (r"collected \d+ items", "#BBBBFF"),
        "pytest_summary": (r"short test summary info", "#FFFF44"),
        "pytest_line": (r"={4,}", "#666666"),
        "pytest_testcase": (r"\bdef test_\w+", "#FFFF00"),
    }

    FONT_CONFIG = ("Segoe UI", 10)
    CHUNK_SIZE = 1000

    window_bg = style.lookup("TFrame", "background", default="#1E2526")
    text_fg = style.lookup("TLabel", "foreground", default="#D3D7CF")
    TOOLTIP_STYLE = {
        "background": style.lookup("TFrame", "background", default="#3C3F41"),
        "foreground": style.lookup("TLabel", "foreground", default="#D3D7CF"),
        "font": ("Segoe UI", 8)
    }

    if not Path(logfile).is_file():
        messagebox.showerror("Error", f"Logfile {logfile} not found.")
        return

    log_dir = Path(logfile).parent
    log_files = sorted([f for f in log_dir.glob("*.log") if f.is_file()])
    if not log_files:
        messagebox.showerror("Error", "No log files found in the directory.")
        return
    current_log_index = log_files.index(Path(logfile)) if Path(logfile) in log_files else 0
    logfile = str(log_files[current_log_index])

    win = tk.Toplevel(master)
    win.title(f"{WINDOW_TITLE} - {Path(logfile).name}")
    win.geometry(WINDOW_SIZE)
    icon = Path(__file__).parent / "autoPy++.ico"
    if icon.exists():
        win.iconbitmap(icon)
    win.minsize(*map(int, MIN_WINDOW_SIZE.split("x")))
    win.resizable(True, True)
    win.configure(bg=window_bg)

    main_frame = ttk.Frame(win, padding=10)
    main_frame.pack(fill="both", expand=True)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(2, weight=1)
    main_frame.rowconfigure(4, weight=0)

    log_path = Path(logfile)
    file_info = f"Logfile: {log_path.name} | Size: {log_path.stat().st_size / 1024:.2f} KB | Created: {datetime.fromtimestamp(log_path.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')}"
    file_info_label = ttk.Label(main_frame, text=file_info, font=("Segoe UI", 9), foreground=text_fg)
    file_info_label.pack(anchor="w", pady=(0, 5))

    stats_label = ttk.Label(main_frame, text="", foreground=text_fg)
    stats_label.pack(anchor="w", pady=(5, 0))

    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill="x", pady=(0, 10))

    log_selector = ttk.Combobox(btn_frame, values=[f.name for f in log_files], state="readonly")
    log_selector.pack(side="left", padx=5)
    log_selector.current(current_log_index)
    def change_logfile(event):
        nonlocal logfile, current_log_index
        current_log_index = log_selector.current()
        logfile = str(log_files[current_log_index])
        log_path = Path(logfile)
        file_info = f"Logfile: {log_path.name} | Size: {log_path.stat().st_size / 1024:.2f} KB | Created: {datetime.fromtimestamp(log_path.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')}"
        file_info_label.config(text=file_info)
        win.title(f"{WINDOW_TITLE} - {log_path.name}")
        load_logfile_async()
    log_selector.bind("<<ComboboxSelected>>", change_logfile)

    def open_logfile():
        os.startfile(logfile)
    def delete_logfile():
        if messagebox.askyesno("Confirm", f"Delete logfile {logfile}?"):
            try:
                Path(logfile).unlink()
                messagebox.showinfo("Success", "Logfile deleted.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Deletion failed: {e}")
    def export_errors():
        error_tags = ["failed", "not_found", "permission_denied", "pytest_fail", "pytest_error"]
        error_patterns = [KEYWORD_PATTERNS[tag][0] for tag in error_tags if tag in KEYWORD_PATTERNS]
        errors: list[str] = []
        for log_line in lines:
            if any(re.search(pattern, log_line) for pattern in error_patterns):
                errors.append(log_line.strip())
        if errors:
            with open("errors_export.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(errors))
            messagebox.showinfo("Success", "Errors exported to errors_export.txt")
        else:
            messagebox.showinfo("Info", "No errors found to export.")
    buttons = [
        ("Open Logfile", open_logfile, "Opens the logfile in the default editor"),
        ("Delete Logfile", delete_logfile, "Permanently deletes the logfile"),
        ("Export Errors", export_errors, "Exports errors to a text file"),
    ]

    tooltip_label = None
    def show_tooltip(event, text):
        nonlocal tooltip_label
        if tooltip_label:
            tooltip_label.destroy()
        tooltip_label = tk.Label(win, text=text, **TOOLTIP_STYLE, relief="solid", borderwidth=1)
        tooltip_label.place(x=event.x_root - win.winfo_rootx() + 10, y=event.y_root - win.winfo_rooty() + 20)
    def hide_tooltip(event):
        nonlocal tooltip_label
        if tooltip_label:
            tooltip_label.destroy()
            tooltip_label = None
    for btn_text, command, tooltip in buttons:
        btn = ttk.Button(btn_frame, text=btn_text, command=command, style="TButton")
        btn.pack(side="left", padx=5, fill="x", expand=True)
        btn.bind('<Enter>', lambda e, t=tooltip: show_tooltip(e, t))
        btn.bind('<Leave>', hide_tooltip)

    search_frame = ttk.Frame(main_frame)
    search_frame.pack(fill="x", pady=(0, 5))
    ttk.Label(search_frame, text="Search:", foreground=text_fg).pack(side="left", padx=(0, 5))
    search_var = tk.StringVar()
    common_terms = config.get('saved_searches', ["error", "warning", "exception", "failed", "success", "monkeypatch", "capsys", "fixture", "assert"])
    search_entry = ttk.Combobox(search_frame, textvariable=search_var, values=common_terms)
    search_entry.pack(side="left", fill="x", expand=True)
    regex_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(search_frame, text="Regex", variable=regex_var).pack(side="left", padx=5)
    case_sensitive_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(search_frame, text="Case Sensitive", variable=case_sensitive_var).pack(side="left", padx=5)
    def save_search_term():
        term = search_var.get().strip()
        if term and term not in common_terms:
            common_terms.append(term)
            search_entry['values'] = common_terms
            config['saved_searches'] = common_terms
            save_config(config)
    ttk.Button(search_frame, text="Save Search", command=save_search_term).pack(side="left", padx=5)
    next_match_btn = ttk.Button(search_frame, text="Next Match", command=lambda: navigate_matches("next"))
    next_match_btn.pack(side="left", padx=5)
    prev_match_btn = ttk.Button(search_frame, text="Prev Match", command=lambda: navigate_matches("prev"))
    prev_match_btn.pack(side="left", padx=5)
    next_log_btn = ttk.Button(search_frame, text="Next Log", command=lambda: navigate_log_files("next"))
    next_log_btn.pack(side="left", padx=5)
    prev_log_btn = ttk.Button(search_frame, text="Prev Log", command=lambda: navigate_log_files("prev"))
    prev_log_btn.pack(side="left", padx=5)

    ttk.Label(search_frame, text="Custom Pattern:", foreground=text_fg).pack(side="left", padx=5)
    custom_pattern_var = tk.StringVar()
    custom_entry = ttk.Entry(search_frame, textvariable=custom_pattern_var)
    custom_entry.pack(side="left", padx=5)

    text_frame = ttk.Frame(main_frame)
    text_frame.pack(fill="both", expand=True)
    line_numbers_widget = tk.Text(text_frame, width=4, bg=window_bg, fg=text_fg, font=FONT_CONFIG)
    line_numbers_widget.pack(side="left", fill="y")
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=FONT_CONFIG, bg=window_bg, fg=text_fg, insertbackground=text_fg)
    text_widget.pack(side="left", fill="both", expand=True)
    def on_scroll(*args):
        text_widget.yview(*args)
        line_numbers_widget.yview(*args)
    scrollbar.config(command=on_scroll)
    def on_text_scroll(event):
        line_numbers_widget.yview_moveto(text_widget.yview()[0])
    def on_line_numbers_scroll(event):
        text_widget.yview_moveto(line_numbers_widget.yview()[0])
    text_widget.bind("<MouseWheel>", on_text_scroll)
    line_numbers_widget.bind("<MouseWheel>", on_line_numbers_scroll)
    text_widget.bind("<Button-4>", on_text_scroll)
    text_widget.bind("<Button-5>", on_text_scroll)
    line_numbers_widget.bind("<Button-4>", on_line_numbers_scroll)
    line_numbers_widget.bind("<Button-5>", on_line_numbers_scroll)
    context_menu = tk.Menu(text_widget, tearoff=0)
    context_menu.add_command(label="Copy Line", command=lambda: text_widget.clipboard_append(text_widget.get("insert linestart", "insert lineend")))
    context_menu.add_command(label="Show Context", command=lambda: show_error_context(None))
    text_widget.bind("<Button-3>", lambda e: context_menu.post(e.x_root, e.y_root))
    error_frame = ttk.Frame(main_frame)
    error_frame.pack(fill="x", pady=(5, 0))
    error_listbox = tk.Listbox(error_frame, height=7, bg=window_bg, fg="#FF0000", font=FONT_CONFIG, selectbackground="#4A4A4A")
    error_listbox.pack(side="left", fill="x", expand=True)
    lines: list[str] = []
    last_modified = Path(logfile).stat().st_mtime

    def get_error_recommendation(log_line):
        for key, rec in ERROR_RECOMMENDATIONS.items():
            if re.search(key, log_line, re.IGNORECASE):
                return rec
        return ""

    def load_logfile_chunks(chunk_size=CHUNK_SIZE):
        nonlocal lines
        text_widget.config(state="normal")
        text_widget.delete("1.0", "end")
        line_numbers_widget.delete("1.0", "end")
        try:
            with open(logfile, encoding="utf-8") as f:
                lines[:] = f.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logfile: {e}")
            return
        text_widget.insert("1.0", "".join(lines))
        line_numbers_widget.insert("1.0", "\n".join(str(i) for i in range(1, len(lines) + 1)))
        text_widget.config(state="disabled")
        line_numbers_widget.config(state="disabled")
        apply_highlighting()
        text_widget.see("end")

    def load_logfile_async():
        def load():
            load_logfile_chunks()
            win.after(0, lambda: [apply_highlighting(), update_button_states()])
        threading.Thread(target=load, daemon=True).start()
    def check_file_changes():
        nonlocal last_modified
        try:
            current_mtime = Path(logfile).stat().st_mtime
            if current_mtime > last_modified:
                last_modified = current_mtime
                load_logfile_async()
        except FileNotFoundError:
            return
        win.after(1000, check_file_changes)

    def update_line_highlight():
        text_widget.config(state="normal")
        text_widget.tag_remove("highlight_line", "1.0", "end")
        current_index = text_widget.index("insert")
        line_num = int(current_index.split(".")[0])
        text_widget.tag_add("highlight_line", f"{line_num}.0", f"{line_num + 1}.0")
        if "search" in text_widget.tag_names():
            text_widget.tag_raise("highlight_line", "search")
        else:
            text_widget.tag_raise("highlight_line")
        text_widget.config(state="disabled")

    error_positions: list[str] = []

    def apply_highlighting():
        nonlocal error_positions
        error_positions.clear()
        text_widget.config(state="normal")
        stats = {tag: 0 for tag in KEYWORD_PATTERNS}
        error_listbox.delete(0, "end")
        critical_tags = ["failed", "permission_denied", "not_found", "pytest_fail", "pytest_error"]
        text_widget.tag_configure("highlight_line", background="#4A4A4A")
        for tag, (pattern, color) in KEYWORD_PATTERNS.items():
            text_widget.tag_configure(tag, foreground=color, font=("Segoe UI", 10, "bold"))
            for i, log_line in enumerate(lines, 1):
                for match in re.finditer(pattern, log_line):
                    text_widget.tag_add(tag, f"{i}.{match.start()}", f"{i}.{match.end()}")
                    stats[tag] += 1
                    if tag.startswith("error") or tag in critical_tags:
                        recommendation = get_error_recommendation(log_line)
                        rec_text = f" | First Aid: {recommendation}" if recommendation else ""
                        error_listbox.insert("end", f"Line {i}: {log_line.strip()}{rec_text}")
                        error_positions.append(f"{i}.0")
        # Stacktrace und Testnamen speziell hervorheben
        for i, log_line in enumerate(lines, 1):
            # Pytest-Trace
            if re.match(r"\s+E\s+", log_line):
                text_widget.tag_add("pytest_trace", f"{i}.0", f"{i}.end")
            # Testfunktion
            if re.search(r"\bdef test_\w+", log_line):
                text_widget.tag_add("pytest_testcase", f"{i}.0", f"{i}.end")
        text_widget.tag_configure("value", foreground="#FFFF00")
        for i, log_line in enumerate(lines, 1):
            for match in re.finditer(r"\b0x[0-9a-fA-F]+\b|\b\d{4}-\d{2}-\d{2}\b|\bexit code \d+\b", log_line):
                text_widget.tag_add("value", f"{i}.{match.start()}", f"{i}.{match.end()}")
        text_widget.tag_configure("custom", foreground="#FF00FF")
        apply_custom_pattern()
        stats_text = " | ".join(f"{tag.capitalize()}: {count}" for tag, count in stats.items())
        stats_label.config(text=stats_text)
        text_widget.config(state="disabled")

    def jump_to_error(event):
        text_widget.config(state="normal")
        text_widget.tag_remove("highlight_line", "1.0", "end")
        selection = error_listbox.curselection()
        if selection and len(error_positions) > selection[0]:
            index = selection[0]
            line_pos = error_positions[index]
            try:
                line_num = int(line_pos.split(".")[0])
                text_widget.see(line_pos)
                text_widget.mark_set("insert", line_pos)
                text_widget.tag_add("highlight_line", f"{line_num}.0", f"{line_num + 1}.0")
                if "search" in text_widget.tag_names():
                    text_widget.tag_raise("highlight_line", "search")
                else:
                    text_widget.tag_raise("highlight_line")
            except ValueError as e:
                print(f"Error parsing line position {line_pos}: {e}")
        else:
            print("No valid selection or error_positions empty")
        text_widget.config(state="disabled")
    error_listbox.bind("<Double-1>", jump_to_error)

    def apply_custom_pattern():
        text_widget.config(state="normal")
        text_widget.tag_remove("custom", "1.0", "end")
        pattern = custom_pattern_var.get().strip()
        if pattern:
            try:
                for i, log_line in enumerate(lines, 1):
                    for match in re.finditer(pattern, log_line, re.IGNORECASE):
                        text_widget.tag_add("custom", f"{i}.{match.start()}", f"{i}.{match.end()}")
            except re.error:
                messagebox.showerror("Invalid Pattern", "Invalid regular expression.")
        text_widget.config(state="disabled")
    custom_pattern_var.trace_add("write", lambda *_: apply_custom_pattern())

    text_widget.bind("<Button-1>", lambda event: [text_widget.mark_set("insert", text_widget.index("@%d,%d" % (event.x, event.y))), update_line_highlight()])
    text_widget.bind("<KeyPress>", lambda event: [win.after(0, update_line_highlight)])

    matches: list[str] = []
    def search_text(*args):
        text_widget.config(state="normal")
        text_widget.tag_remove("search", "1.0", "end")
        query = search_var.get().strip()
        if not query:
            text_widget.config(state="disabled")
            return
        text_widget.tag_configure("search", background="#FFFF00")
        matches.clear()
        try:
            flags = 0 if case_sensitive_var.get() else re.IGNORECASE
            pattern = re.compile(query, flags) if regex_var.get() else re.compile(re.escape(query), flags)
            for i, log_line in enumerate(lines, 1):
                for match in pattern.finditer(log_line):
                    start = f"{i}.{match.start()}"
                    end = f"{i}.{match.end()}"
                    text_widget.tag_add("search", start, end)
                    matches.append(start)
            if matches:
                text_widget.see(matches[0])
                text_widget.tag_raise("search")
        except re.error:
            messagebox.showerror("Invalid Regex", "Invalid regular expression.")
        text_widget.config(state="disabled")

    def navigate_matches(direction):
        if not matches:
            messagebox.showinfo("Info", "No search matches found.")
            return
        current = text_widget.index("insert")
        next_match = matches[0]
        if direction == "next":
            for m in matches:
                if m > current:
                    next_match = m
                    break
        else:
            for m in reversed(matches):
                if m < current:
                    next_match = m
                    break
        text_widget.see(next_match)
        text_widget.mark_set("insert", next_match)
        update_line_highlight()

    def navigate_log_files(direction):
        nonlocal logfile, current_log_index
        new_index = current_log_index + (1 if direction == "next" else -1)
        if 0 <= new_index < len(log_files):
            logfile = str(log_files[new_index])
            current_log_index = new_index
            log_selector.current(current_log_index)
            log_path = Path(logfile)
            file_info = f"Logfile: {log_path.name} | Size: {log_path.stat().st_size / 1024:.2f} KB | Created: {datetime.fromtimestamp(log_path.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')}"
            file_info_label.config(text=file_info)
            win.title(f"{WINDOW_TITLE} - {log_path.name}")
            load_logfile_async()
        update_button_states()

    def update_button_states():
        next_log_btn.config(state="normal" if current_log_index < len(log_files) - 1 else "disabled")
        prev_log_btn.config(state="normal" if current_log_index > 0 else "disabled")

    search_var.trace_add("write", search_text)
    search_entry.bind("<Return>", search_text)

    def show_error_context(event):
        index = text_widget.index("@%d,%d" % (event.x, event.y)) if event else text_widget.index("insert")
        line = int(index.split(".")[0])
        context_lines = 2
        start = max(1, line - context_lines)
        end = min(len(lines) + 1, line + context_lines + 1)
        context = "\n".join(lines[start-1:end-1])
        messagebox.showinfo("Error Context", f"Line {line}:\n{context}")

    text_widget.bind("<Double-1>", show_error_context)

    # Fancy: Fehler Tooltip für Listbox mit Empfehlungen
    def error_listbox_tooltip(event):
        index = error_listbox.nearest(event.y)
        if 0 <= index < error_listbox.size():
            line = error_listbox.get(index)
            rec = get_error_recommendation(line)
            if rec:
                show_tooltip(event, f"{line}\n\nTipp: {rec}")
            else:
                show_tooltip(event, line)
    error_listbox.bind("<Motion>", error_listbox_tooltip)
    error_listbox.bind("<Leave>", hide_tooltip)

    load_logfile_async()
    update_button_states()
    check_file_changes()
