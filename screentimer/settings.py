import sys
import tkinter as tk
from tkinter import messagebox
from screentimer.config import AppConfig, ConfigStore, hash_password

_FONT_FAMILY = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI"


class SettingsWindow:
    """Startup and in-session configuration UI."""

    def __init__(self, root: tk.Tk, store: ConfigStore, on_start, on_apply=None):
        self._root = root
        self._store = store
        self._on_start = on_start
        self._on_apply = on_apply or on_start
        self._saved_hash = None
        self._running = False  # True after timer has been started once

        root.title("ScreenTimer — Settings")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        self._build_ui()
        self._load_saved()

    def _build_ui(self):
        root = self._root
        pad = {"padx": 16, "pady": 6}

        tk.Label(root, text="ScreenTimer", font=(_FONT_FAMILY, 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(20, 10))

        tk.Label(root, text="Lock interval (minutes):").grid(row=1, column=0, sticky="e", **pad)
        self._interval_var = tk.StringVar(value="30")
        tk.Spinbox(root, from_=1, to=480, textvariable=self._interval_var,
                   width=6, font=(_FONT_FAMILY, 11)).grid(row=1, column=1, sticky="w", **pad)

        tk.Label(root, text="Auto-unlock delay (minutes):").grid(row=2, column=0, sticky="e", **pad)
        self._auto_var = tk.StringVar(value="5")
        tk.Spinbox(root, from_=1, to=60, textvariable=self._auto_var,
                   width=6, font=(_FONT_FAMILY, 11)).grid(row=2, column=1, sticky="w", **pad)

        tk.Label(root, text="Daily screen limit (mins, 0=off):").grid(row=3, column=0, sticky="e", **pad)
        self._daily_var = tk.StringVar(value="0")
        tk.Spinbox(root, from_=0, to=1439, textvariable=self._daily_var,
                   width=6, font=(_FONT_FAMILY, 11)).grid(row=3, column=1, sticky="w", **pad)

        tk.Label(root, text="Parent password:").grid(row=4, column=0, sticky="e", **pad)
        self._pw_entry = tk.Entry(root, show="*", font=(_FONT_FAMILY, 11), width=20)
        self._pw_entry.grid(row=4, column=1, sticky="w", **pad)

        self._pw_hint = tk.Label(root, text="", font=(_FONT_FAMILY, 9), fg="#777777")
        self._pw_hint.grid(row=5, column=0, columnspan=2)

        self._action_btn = tk.Button(root, text="Start", font=(_FONT_FAMILY, 12, "bold"),
                                     width=12, command=self._on_action_click)
        self._action_btn.grid(row=6, column=0, columnspan=2, pady=(14, 20))

    def _load_saved(self):
        cfg = self._store.load()
        if cfg:
            self._interval_var.set(str(cfg.lock_interval_mins))
            self._auto_var.set(str(cfg.auto_unlock_mins))
            self._daily_var.set(str(cfg.daily_limit_mins))
            self._saved_hash = cfg.password_hash
            self._pw_hint.config(text="Leave password blank to keep saved password")

    def show_for_running(self):
        """Show settings while timer is running. Requires parent password."""
        if not self._ask_password():
            return
        self._running = True
        self._action_btn.config(text="Apply")
        self._load_saved()
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()

    def _ask_password(self) -> bool:
        if not self._saved_hash:
            return True

        dialog = tk.Toplevel(self._root)
        dialog.title("Parent Password Required")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self._root)

        result = [False]

        tk.Label(dialog, text="Enter parent password to change settings:",
                 font=(_FONT_FAMILY, 11)).pack(padx=20, pady=(16, 8))

        entry = tk.Entry(dialog, show="*", font=(_FONT_FAMILY, 11), width=20)
        entry.pack(padx=20, pady=(0, 4))
        entry.focus_set()

        error_lbl = tk.Label(dialog, text="", fg="#ff4444", font=(_FONT_FAMILY, 10))
        error_lbl.pack()

        def check():
            if hash_password(entry.get()) == self._saved_hash:
                result[0] = True
                dialog.destroy()
            else:
                error_lbl.config(text="Incorrect password")
                entry.delete(0, tk.END)

        entry.bind("<Return>", lambda e: check())
        tk.Button(dialog, text="OK", command=check,
                  font=(_FONT_FAMILY, 11)).pack(pady=(8, 16))

        self._root.wait_window(dialog)
        return result[0]

    def _on_action_click(self):
        try:
            interval = int(self._interval_var.get())
            auto = int(self._auto_var.get())
            daily = int(self._daily_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "All fields must be whole numbers.")
            return

        if interval < 1 or auto < 1:
            messagebox.showerror("Invalid input", "Lock interval and auto-unlock must be at least 1 minute.")
            return

        if daily < 0 or daily > 1439:
            messagebox.showerror("Invalid input", "Daily limit must be between 0 and 1439 minutes.")
            return

        typed_pw = self._pw_entry.get()
        if typed_pw:
            password_hash = hash_password(typed_pw)
        elif self._saved_hash:
            password_hash = self._saved_hash
        else:
            messagebox.showerror("Password required", "Please enter a parent password.")
            return

        cfg = AppConfig(
            lock_interval_mins=interval,
            auto_unlock_mins=auto,
            password_hash=password_hash,
            daily_limit_mins=daily,
        )
        self._store.save(cfg)
        self._saved_hash = password_hash
        self._pw_hint.config(text="Leave password blank to keep saved password")
        self._root.withdraw()

        if self._running:
            self._on_apply(cfg)
        else:
            self._running = True
            self._action_btn.config(text="Apply")
            self._on_start(cfg)
