import tkinter as tk
from tkinter import messagebox
from screentimer.config import AppConfig, ConfigStore, hash_password


class SettingsWindow:
    """Startup configuration UI. Calls on_start(config) when the parent clicks Start."""

    def __init__(self, root: tk.Tk, store: ConfigStore, on_start):
        self._root = root
        self._store = store
        self._on_start = on_start
        self._saved_hash = None

        root.title("ScreenTimer — Settings")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        self._build_ui()
        self._load_saved()

    def _build_ui(self):
        root = self._root
        pad = {"padx": 16, "pady": 6}

        tk.Label(root, text="ScreenTimer", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(20, 10))

        tk.Label(root, text="Lock interval (minutes):").grid(row=1, column=0, sticky="e", **pad)
        self._interval_var = tk.StringVar(value="30")
        tk.Spinbox(root, from_=1, to=480, textvariable=self._interval_var,
                   width=6, font=("Segoe UI", 11)).grid(row=1, column=1, sticky="w", **pad)

        tk.Label(root, text="Auto-unlock delay (minutes):").grid(row=2, column=0, sticky="e", **pad)
        self._auto_var = tk.StringVar(value="5")
        tk.Spinbox(root, from_=1, to=60, textvariable=self._auto_var,
                   width=6, font=("Segoe UI", 11)).grid(row=2, column=1, sticky="w", **pad)

        tk.Label(root, text="Parent password:").grid(row=3, column=0, sticky="e", **pad)
        self._pw_entry = tk.Entry(root, show="*", font=("Segoe UI", 11), width=20)
        self._pw_entry.grid(row=3, column=1, sticky="w", **pad)

        self._pw_hint = tk.Label(root, text="", font=("Segoe UI", 9), fg="#777777")
        self._pw_hint.grid(row=4, column=0, columnspan=2)

        tk.Button(root, text="Start", font=("Segoe UI", 12, "bold"),
                  width=12, command=self._on_start_click).grid(
            row=5, column=0, columnspan=2, pady=(14, 20))

    def _load_saved(self):
        cfg = self._store.load()
        if cfg:
            self._interval_var.set(str(cfg.lock_interval_mins))
            self._auto_var.set(str(cfg.auto_unlock_mins))
            self._saved_hash = cfg.password_hash
            self._pw_hint.config(text="Leave password blank to keep saved password")

    def _on_start_click(self):
        try:
            interval = int(self._interval_var.get())
            auto = int(self._auto_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Lock interval and auto-unlock delay must be whole numbers.")
            return

        if interval < 1 or auto < 1:
            messagebox.showerror("Invalid input", "Values must be at least 1 minute.")
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
        )
        self._store.save(cfg)
        self._root.withdraw()
        self._on_start(cfg)
