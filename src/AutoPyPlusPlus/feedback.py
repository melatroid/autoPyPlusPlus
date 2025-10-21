import os
import base64
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import hashlib, hmac, json, time, inspect

try:
    SCRIPT_DIR = Path(__file__).resolve().parent
except Exception:
    SCRIPT_DIR = Path(os.getcwd()).resolve()

FB_PATH = SCRIPT_DIR / "fb.ini"
FB_TOKEN = b"fb_done_v1"

_DEPLOY_HASH = ""

def _self_hash() -> str:
    try:
        with open(__file__, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

def _integrity_ok() -> bool:
    if _DEPLOY_HASH and _DEPLOY_HASH != _self_hash():
        return False
    try:
        src = (
            inspect.getsource(show_feedback_dialog) +
            inspect.getsource(_write_flag) +
            inspect.getsource(feedback_is_done)
        )
        hashlib.sha256(src.encode()).hexdigest()
        return True
    except Exception:
        return True

def _debug_suspected() -> bool:
    if sys.gettrace() is not None:
        return True
    for v in ("PYTHONINSPECT", "PYTHONFAULTHANDLER"):
        if os.environ.get(v):
            return True
    return False

def _derive_key() -> bytes:
    base = (str(SCRIPT_DIR) + "|" + sys.executable + "|" + sys.version + "|" + os.name).encode("utf-8","ignore")
    return hashlib.sha256(base).digest()

def _seal_dict(d: dict) -> bytes:
    raw = json.dumps(d, separators=(",", ":")).encode()
    tag = hmac.new(_derive_key(), raw, hashlib.sha256).digest()
    return base64.b64encode(tag + raw)

def _open_sealed(b64: bytes) -> dict:
    blob = base64.b64decode(b64)
    tag, raw = blob[:32], blob[32:]
    if hmac.new(_derive_key(), raw, hashlib.sha256).digest() != tag:
        raise ValueError("bad flag")
    return json.loads(raw.decode())

def _monotonic_token(seconds: int) -> str:
    return hashlib.sha256(f"{time.monotonic():.6f}|{seconds}".encode()).hexdigest()[:12]

MASTER_KEY_ITER = 200_000
MASTER_KEY_SALT_B64 = "/uN9ZDrEaTzAj3N/xmgPdQ=="
MASTER_KEY_HASH_B64 = "N8RmPmga+tWIyVi2VheG5DHNvUM8YZnxiVzdjsm7K5U="

def _verify_master_key(secret: str) -> bool:
    try:
        salt = base64.b64decode(MASTER_KEY_SALT_B64)
        want = base64.b64decode(MASTER_KEY_HASH_B64)
        got = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, MASTER_KEY_ITER, dklen=32)
        return hmac.compare_digest(got, want)
    except Exception:
        return False

def _prompt_master_key(parent: tk.Misc, on_success):
    win = tk.Toplevel(parent)
    win.title("Master Key Required")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    frame = ttk.Frame(win, padding=12)
    frame.pack(expand=True, fill="both")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    ttk.Label(frame, text="Enter Master Key:", justify="center", anchor="center")\
        .grid(row=0, column=0, columnspan=2, sticky="ew")
    var = tk.StringVar()
    entry = ttk.Entry(frame, textvariable=var, show="*")
    entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 6))
    status = ttk.Label(frame, text="", foreground="#a00", justify="center", anchor="center")
    status.grid(row=2, column=0, columnspan=2, sticky="ew")

    attempts = {"n": 0, "max": 3}

    def _try_ok(*_):
        s = var.get()
        if _verify_master_key(s):
            try:
                win.grab_release()
            except Exception:
                pass
            win.destroy()
            on_success()
        else:
            attempts["n"] += 1
            if attempts["n"] >= attempts["max"]:
                status.config(text="Too many failed attempts. Operation aborted.")
                ok_btn.configure(state="disabled")
                entry.configure(state="disabled")
                cancel_btn.configure(text="Close")
            else:
                status.config(text=f"Incorrect. Remaining attempts: {attempts['max']-attempts['n']}")

    def _cancel():
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()

    btn_row = ttk.Frame(frame)
    btn_row.grid(row=3, column=0, columnspan=2, pady=(10, 0))
    ok_btn = ttk.Button(btn_row, text="OK", command=_try_ok)
    cancel_btn = ttk.Button(btn_row, text="Cancel", command=_cancel)
    ok_btn.pack(side="left", padx=(0, 6))
    cancel_btn.pack(side="left")

    win.bind("<Return>", _try_ok)
    win.bind("<Escape>", lambda e: _cancel())
    entry.focus_set()

    win.update_idletasks()
    pad_w, pad_h = 40, 40
    width = max(320, frame.winfo_reqwidth() + pad_w)
    height = frame.winfo_reqheight() + pad_h
    x = (parent.winfo_screenwidth() // 2) - (width // 2)
    y = (parent.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32   = ctypes.WinDLL("user32", use_last_error=True)

    CRYPTPROTECT_UI_FORBIDDEN = 0x01

    def _get_optional_entropy() -> bytes:
        try:
            user = os.getlogin()
        except Exception:
            user = ""
        return (user + "|" + str(SCRIPT_DIR)).encode("utf-8","ignore")

    def _protect_dpapi(raw: bytes) -> bytes:
        in_blob = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.POINTER(ctypes.c_byte)))
        out_blob = DATA_BLOB()
        opt = _get_optional_entropy()
        opt_blob = DATA_BLOB(len(opt), ctypes.cast(ctypes.create_string_buffer(opt), ctypes.POINTER(ctypes.c_byte)))
        if not crypt32.CryptProtectData(ctypes.byref(in_blob), None, ctypes.byref(opt_blob), None, None, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(out_blob)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            kernel32.LocalFree(out_blob.pbData)

    def _unprotect_dpapi(enc: bytes) -> bytes:
        in_blob = DATA_BLOB(len(enc), ctypes.cast(ctypes.create_string_buffer(enc), ctypes.POINTER(ctypes.c_byte)))
        out_blob = DATA_BLOB()
        opt = _get_optional_entropy()
        opt_blob = DATA_BLOB(len(opt), ctypes.cast(ctypes.create_string_buffer(opt), ctypes.POINTER(ctypes.c_byte)))
        if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, ctypes.byref(opt_blob), None, None, 0, ctypes.byref(out_blob)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            kernel32.LocalFree(out_blob.pbData)


    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextW       = user32.GetWindowTextW
    IsWindowVisible      = user32.IsWindowVisible
    EnumWindows          = user32.EnumWindows
    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    OpenProcess          = kernel32.OpenProcess
    CloseHandle          = kernel32.CloseHandle
    QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def _proc_image_path(pid: int) -> str:
        h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return ""
        try:
            size = wintypes.DWORD(260)
            buf = ctypes.create_unicode_buffer(260)
            if QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return buf.value
            return ""
        finally:
            CloseHandle(h)

    def _edge_visible_now() -> bool:
        found = {"ok": False}
        def _cb(hwnd, lparam):
            try:
                if not IsWindowVisible(hwnd):
                    return True
                length = GetWindowTextLengthW(hwnd)
                title = ""
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value or ""
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value:
                    path = _proc_image_path(pid.value).lower()
                    if path.endswith("\\msedge.exe") or path.endswith("/msedge.exe"):
                        found["ok"] = True
                        return False
            except Exception:
                pass
            return True
        EnumWindows(EnumProc(_cb), 0)
        return found["ok"]

else:
    def _protect_dpapi(raw: bytes) -> bytes:
        tag = hmac.new(_derive_key(), raw, hashlib.sha256).digest()
        return tag + raw
    def _unprotect_dpapi(enc: bytes) -> bytes:
        tag, raw = enc[:32], enc[32:]
        if hmac.new(_derive_key(), raw, hashlib.sha256).digest() != tag:
            raise ValueError("bad token")
        return raw
    def _edge_visible_now() -> bool:
        return True

def _write_flag(countdown_seconds: int, started_token: str, last_seen_ts: float):
    try:
        if _debug_suspected() or not _integrity_ok():
            return
        if os.name == "nt":
            if not _edge_visible_now():
                return
            if (time.time() - float(last_seen_ts or 0)) > 10.0:
                return
        blob = _protect_dpapi(FB_TOKEN)
        payload = {
            "v": 2,
            "token": base64.b64encode(blob).decode(),
            "path": str(SCRIPT_DIR),
            "py": sys.version.split()[0],
            "ts": int(time.time()),
            "ct": int(countdown_seconds),
            "st": str(started_token or ""),
            "bw": "edge_ok" if (os.name != "nt" or _edge_visible_now()) else "none",
            "ls": float(last_seen_ts or 0)
        }
        with open(FB_PATH, "wb") as f:
            f.write(_seal_dict(payload))
    except Exception as e:
        print("Failed to write fb.ini:", e, file=sys.stderr)

def feedback_is_done() -> bool:
    try:
        with open(FB_PATH, "rb") as f:
            data = f.read()
        try:
            info = _open_sealed(data)
            if info.get("path") != str(SCRIPT_DIR):
                return False
            blob = base64.b64decode(info["token"])
            raw = _unprotect_dpapi(blob)
            return raw == FB_TOKEN
        except Exception:
            try:
                blob = base64.b64decode(data)
                raw = _unprotect_dpapi(blob)
                return raw == FB_TOKEN
            except Exception:
                return False
    except Exception:
        return False

def show_feedback_dialog(
    master: tk.Misc,
    style=None,
    theme_func=lambda *args, **kwargs: None,
    image_path: str = "git.png",
    note_text: str = (
        "1) You can skip after 10 seconds.\n"
        "2) This process is like a registration.\n"
        "3) Don't give feedback when you try,\n"
        "   this software for the first time.\n"
        "4) No data will be transmitted.\n"
        "5) User feedback is a one-time process."
    ),
    url: str = "https://forms.gle/QTuEyava7t4bFL4JA",
    countdown_seconds: int = 15,
    hide_close_seconds: int = 10,
) -> bool:
    if feedback_is_done():
        return False
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    win = tk.Toplevel(master)
    win.title("Feedback")
    win.resizable(False, False)
    win.transient(master)
    win.grab_set()
    try:
        win.iconbitmap("autoPy++.ico")
    except Exception:
        pass
    if theme_func:
        theme_func(style, win)
    frame = ttk.Frame(win, padding=12)
    frame.pack(expand=True, fill="both")
    frame.grid_columnconfigure(0, weight=1)
    row = 0
    try:
        from PIL import Image, ImageTk
        img_raw = Image.open(image_path)
        max_w, max_h = 280, 280
        w, h = img_raw.size
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img_raw = img_raw.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        _img_ref = ImageTk.PhotoImage(img_raw)
        lbl = ttk.Label(frame, image=_img_ref)
        lbl.image = _img_ref
        lbl.grid(row=row, column=0, pady=(0, 10))
        row += 1
    except Exception:
        try:
            _img_ref = tk.PhotoImage(file=image_path)
            lbl = ttk.Label(frame, image=_img_ref)
            lbl.image = _img_ref
            lbl.grid(row=row, column=0, pady=(0, 10))
            row += 1
        except Exception:
            pass
    if note_text:
        ttk.Label(frame, text=note_text, wraplength=360, justify="center", anchor="center")\
            .grid(row=row, column=0, sticky="ew", pady=(0, 8))
        row += 1
    status_lbl = ttk.Label(frame, text="", justify="center", anchor="center")
    status_lbl.grid(row=row, column=0, sticky="ew", pady=(0, 8))
    row += 1
    btn = ttk.Button(frame, text="Give Feedback")
    btn.grid(row=row, column=0, sticky="ew")
    row += 1
    close_btn = ttk.Button(frame, text="Close", state="disabled")
    close_btn.grid(row=row, column=0, pady=(8, 0))
    row += 1
    countdown_after_id = {"id": None}
    started_token = {"val": ""}
    last_seen_ts  = {"val": 0.0}
    close_enabled = {"ok": False}
    close_countdown_id = {"id": None}

    def _enable_close():
        if not close_enabled["ok"]:
            close_btn.configure(state="normal")
            close_enabled["ok"] = True
            status_lbl.config(text="You can close this window now if necessary.", justify="center", anchor="center")

    def _close_tick(rem):
        if not win.winfo_exists():
            return
        if rem <= 0:
            close_countdown_id["id"] = None
            _enable_close()
        else:
            status_lbl.config(text=f"Close available in … {rem}s", justify="center", anchor="center")
            close_countdown_id["id"] = win.after(1000, _close_tick, rem - 1)

    def _on_close():
        if not close_enabled["ok"]:
            return
        if countdown_after_id["id"] is not None:
            try:
                win.after_cancel(countdown_after_id["id"])
            except Exception:
                pass
            countdown_after_id["id"] = None
        if close_countdown_id["id"] is not None:
            try:
                win.after_cancel(close_countdown_id["id"])
            except Exception:
                pass
            close_countdown_id["id"] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)
    win.bind("<Escape>", lambda e: _on_close())
    close_btn.configure(command=_on_close)

    def _set_done_and_update():
        def _on_master_ok():
            try:
                if os.name == "nt" and _edge_visible_now():
                    last_seen_ts["val"] = time.time()
            except Exception:
                pass

            _write_flag(countdown_seconds, started_token["val"], last_seen_ts["val"])

            if not win.winfo_exists():
                return
            is_ok = True
            try:
                is_ok = (os.name != "nt") or (_edge_visible_now() and (time.time() - last_seen_ts["val"] <= 10.0))
            except Exception:
                pass

            msg = (
                "Thank you! This prompt will not be shown again."
                if is_ok else
                "Thank you! Note: Keep Microsoft Edge open with the form until the countdown ends."
            )
            status_lbl.config(text=msg, justify="center", anchor="center")

        _prompt_master_key(win, _on_master_ok)


    def _tick(remaining: int):
        if not win.winfo_exists():
            return
        try:
            if _edge_visible_now():
                last_seen_ts["val"] = time.time()
        except Exception:
            pass
        status_lbl.config(text=f"Please keep Edge open … {remaining}s", justify="center", anchor="center")
        if remaining <= 0:
            countdown_after_id["id"] = None
            _set_done_and_update()
        else:
            countdown_after_id["id"] = win.after(1000, _tick, remaining - 1)

    def _start_countdown():
        try:
            if _edge_visible_now():
                last_seen_ts["val"] = time.time()
        except Exception:
            pass
        _tick(countdown_seconds)

    def _open_form():
        if os.name == "nt":
            try:
                os.startfile(f"microsoft-edge:{url}")
            except Exception:
                try:
                    webbrowser.get("edge").open(url, new=1)
                except Exception:
                    webbrowser.open_new(url)
        else:
            webbrowser.open_new(url)
        btn.configure(state="disabled")
        status_lbl.config(text=f"Opening Microsoft Edge… countdown started ({countdown_seconds}s).", justify="center", anchor="center")
        started_token["val"] = _monotonic_token(countdown_seconds)
        _start_countdown()

    btn.configure(command=_open_form)
    win.bind("<Return>", lambda e: _open_form())
    btn.focus_set()
    win.update_idletasks()
    pad_w, pad_h = 40, 40
    width = max(260, frame.winfo_reqwidth() + pad_w)
    height = frame.winfo_reqheight() + pad_h
    x = (master.winfo_screenwidth() // 2) - (width // 2)
    y = (master.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    _close_tick(hide_close_seconds)
    return True
