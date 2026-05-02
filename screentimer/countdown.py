import sys
import tkinter as tk

_FONT_FAMILY = "Helvetica Neue" if sys.platform == "darwin" else "Segoe UI"


class CountdownWidget:
    """Small always-on-top window showing time until next break and daily usage."""

    def __init__(self, root: tk.Tk, on_open_settings):
        self._win = tk.Toplevel(root)
        self._win.title("ScreenTimer")
        self._win.attributes("-topmost", True)
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", lambda: None)

        self._lock_label = tk.Label(self._win, text="Starting...",
                                    font=(_FONT_FAMILY, 12, "bold"))
        self._lock_label.pack(padx=16, pady=(10, 2))

        self._daily_label = tk.Label(self._win, text="", font=(_FONT_FAMILY, 10), fg="#555555")
        self._daily_label.pack(padx=16, pady=(0, 4))

        tk.Button(self._win, text="Settings", command=on_open_settings,
                  font=(_FONT_FAMILY, 9)).pack(pady=(2, 10))

    def update_tick(self, remaining_secs: float, used_secs: float, daily_limit_secs: float):
        mins, secs = divmod(int(remaining_secs), 60)
        self._lock_label.config(text=f"Next break in: {mins:02d}:{secs:02d}")
        if daily_limit_secs > 0:
            um, us = divmod(int(used_secs), 60)
            lm, ls = divmod(int(daily_limit_secs), 60)
            self._daily_label.config(text=f"Daily: {um:02d}:{us:02d} / {lm:02d}:{ls:02d}")
        else:
            self._daily_label.config(text="")

    def set_locked(self):
        self._lock_label.config(text="Screen locked")

    def set_daily_limit_reached(self):
        self._lock_label.config(text="Daily limit reached")
        self._daily_label.config(text="Screen time used up for today")
