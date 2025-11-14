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
    "permission denied": "🔒 Permission denied. First Aid: 1) Restart system 2) Check file/folder permissions.",
    "not found": "🔎 Not found. First Aid: Does the file really exist? Verify the path and spelling.",
    "failed": "💥 Failed. First Aid: Scroll up and inspect the first error message.",
    "exit code": "🔢 Exit code detected. First Aid: Check docs/logic for this specific code.",
    "monkeypatch": "🧪 pytest monkeypatch. First Aid: Imported correctly? Scope/fixture usage OK?",
    "capsys": "🧪 pytest capsys. First Aid: Is the 'capsys' fixture passed into the test?",
    "fixture": "🧩 Fixture issue. First Aid: Declared correctly and name matches?",
    "assert ": "✅/❌ Assertion mismatch. First Aid: Compare expected vs actual values.",
    "not defined": "📦 Name not defined. First Aid: Missing import? Typos or circular imports?",
}

# --- message map ---
ERROR_CODE_MAP = {
    # MSVC / Cython build
    "C1083":  "💡 First Aid: setup.py is default in working dir! Also check filename/path & include dirs.",
    "LNK1104":"💡 First Aid: linker cannot open file — close running EXE/DBG and fix lib/output paths.",
    "C2065":  "💡 First Aid: undeclared identifier — header/namespace/import/typo.",
    "C2143":  "💡 First Aid: syntax error (often missing ';' or brace) — check previous line.",
    "C2664":  "💡 First Aid: no matching function call — fix types/signature or conversions.",
    "LNK2001":"💡 First Aid: unresolved external symbol — add/point to the defining .lib/.obj or source.",
    "LNK2019":"💡 First Aid: unresolved external (referenced in function) — missing definition or wrong lib order.",
    "C1001":  "💡 First Aid: internal compiler error — simplify code or update MSVC/toolchain.",
    "C1026":  "💡 First Aid: parser stack overflow — split overly large functions/expressions.",

    # Cython specifics seen on Windows toolchains
    "pyconfig.h(59)": "💡 First Aid: Windows SDK headers missing — install/repair Windows 10/11 SDK + set VC env.",
    "Cannot open include file: 'io.h'": "💡 First Aid: install Windows SDK / correct VC toolset; ensure INCLUDE paths.",
    "cl.exe' failed with exit code 2": "💡 First Aid: fix the first compile error above; verify MSVC Build Tools in PATH.",

    # PyInstaller
    "Failed to execute script": "💡 First Aid: run from console for traceback; add data/paths; bundle files with --add-data.",
    "hidden import": "💡 First Aid: add --hidden-import <mod> or hook; check build/*warn* for missing modules.",
    "ModuleNotFoundError": "💡 First Aid: hidden import not collected — use --hidden-import / edit .spec's hiddenimports.",
    "DLL load failed": "💡 First Aid: install VC++/UCRT runtime; ensure bundled DLLs match OS/arch.",
    "api-ms-win-crt": "💡 First Aid: install ‘Universal CRT’ / Visual C++ Redistributable for your Windows version.",

    # Nuitka
    "Windows SDK must be installed": "💡 First Aid: install Windows 10/11 SDK + C++ workload; use proper Developer Prompt.",
    "scons: ***": "💡 First Aid: toolchain/env issue — verify MSVC/SDK in PATH or try --mingw64.",
    "link @": "💡 First Aid: linker step failed — avoid non-ASCII paths; check lib locations/output perms.",

    # PyArmor
    "No module named 'pytransform'": "💡 First Aid: ship pytransform runtime (folder/DLL) with app; correct import path.",
    "No module named 'pyarmor_runtime'": "💡 First Aid: include pyarmor_runtime_* package output with the build.",
    "this Python version is not supported": "💡 First Aid: obfuscate with matching PyArmor core for target Python/OS.",
    "unauthorized use of script": "💡 First Aid: check PyArmor license/registration and bound machine settings.",
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
        # Optional: catch MSVC lines explicitly (helps show C1083 lines even if no 'failed' token)
        "msvc_fatal": (r"(?i)\bfatal error C\d{4}\b", "#FF2222"),
        "msvc_error": (r"(?i)\berror C\d{4}\b", "#FF4444"),
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

    # Color for help/First Aid lines in the lower console
    HELP_FG = "#FFD700"  # yellow/gold

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
        error_tags = ["failed", "not_found", "permission_denied", "pytest_fail", "pytest_error", "msvc_fatal", "msvc_error"]
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
        # minimalistic: check codes first (substring, case-insensitive)
        ll = log_line.lower()
        for code, tip in ERROR_CODE_MAP.items():
            if code.lower() in ll:
                return tip
        # fallback to generic keywords
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

    # Positions in the text widget for each error; and a mapping from listbox rows to these positions
    error_positions: list[str] = []
    row_to_err_idx: list[int] = []

    def apply_highlighting():
        nonlocal error_positions
        # reset listbox and mappings
        error_listbox.delete(0, "end")
        row_to_err_idx.clear()
        error_positions.clear()

        text_widget.config(state="normal")
        stats = {tag: 0 for tag in KEYWORD_PATTERNS}
        critical_tags = ["failed", "permission_denied", "not_found", "pytest_fail", "pytest_error", "msvc_fatal", "msvc_error"]
        text_widget.tag_configure("highlight_line", background="#4A4A4A")

        # dedupe by source line so each error line is listed once
        added_error_lines: set[int] = set()

        for tag, (pattern, color) in KEYWORD_PATTERNS.items():
            text_widget.tag_configure(tag, foreground=color, font=("Segoe UI", 10, "bold"))
            for i, log_line in enumerate(lines, 1):
                for match in re.finditer(pattern, log_line):
                    text_widget.tag_add(tag, f"{i}.{match.start()}", f"{i}.{match.end()}")
                    stats[tag] += 1
                    if tag.startswith("error") or tag in critical_tags:
                        if i in added_error_lines:
                            continue
                        added_error_lines.add(i)

                        # Base error row
                        base_text = f"Line {i}: {log_line.strip()}"
                        error_listbox.insert("end", base_text)

                        # record target position for this error row
                        error_positions.append(f"{i}.0")
                        row_to_err_idx.append(len(error_positions) - 1)

                        # Optional recommendation row – maps to same error index
                        recommendation = get_error_recommendation(log_line)
                        if recommendation:
                            tip_text = f"   {recommendation}"
                            error_listbox.insert("end", tip_text)
                            tip_idx = error_listbox.size() - 1
                            try:
                                error_listbox.itemconfig(tip_idx, foreground=HELP_FG)
                            except Exception:
                                pass
                            # map tip row to the same error index as the base row
                            row_to_err_idx.append(len(error_positions) - 1)

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
        # Robust: use explicit row->error index mapping
        if not error_positions or error_listbox.size() == 0:
            return

        sel = error_listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        if idx < 0 or idx >= len(row_to_err_idx):
            return

        err_idx = row_to_err_idx[idx]
        if err_idx < 0 or err_idx >= len(error_positions):
            return

        target = error_positions[err_idx]

        text_widget.config(state="normal")
        try:
            text_widget.tag_remove("highlight_line", "1.0", "end")
            line_num = int(target.split(".")[0])
            text_widget.see(target)
            text_widget.mark_set("insert", target)
            text_widget.tag_add("highlight_line", f"{line_num}.0", f"{line_num + 1}.0")
            if "search" in text_widget.tag_names():
                text_widget.tag_raise("highlight_line", "search")
            else:
                text_widget.tag_raise("highlight_line")
        finally:
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
