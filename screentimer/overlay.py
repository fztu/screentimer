import tkinter as tk


class LockOverlay:
    """Fullscreen always-on-top overlay. Call show() to display, hide() to dismiss."""

    def __init__(self, root: tk.Tk, auto_unlock_secs: int, on_password_unlock, on_auto_unlock):
        self._root = root
        self._auto_unlock_secs = auto_unlock_secs
        self._on_password_unlock = on_password_unlock
        self._on_auto_unlock = on_auto_unlock
        self._countdown_remaining = 0
        self._countdown_job = None
        self._visible = False

        self._win = tk.Toplevel(root)
        self._win.withdraw()
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.configure(bg="black")
        self._win.protocol("WM_DELETE_WINDOW", lambda: None)
        self._win.bind("<Alt-F4>", lambda e: "break")

        self._build_ui()

    def _build_ui(self):
        w = self._win

        tk.Label(w, text="Time for a break!", font=("Segoe UI", 36, "bold"),
                 fg="white", bg="black").pack(pady=(120, 20))

        self._countdown_label = tk.Label(w, text="", font=("Segoe UI", 18),
                                          fg="#aaaaaa", bg="black")
        self._countdown_label.pack(pady=(0, 40))

        frame = tk.Frame(w, bg="black")
        frame.pack()

        self._pw_entry = tk.Entry(frame, show="*", font=("Segoe UI", 14), width=20)
        self._pw_entry.pack(side="left", padx=(0, 10))

        tk.Button(frame, text="Unlock", font=("Segoe UI", 12),
                  command=self._try_unlock).pack(side="left")

        self._error_label = tk.Label(w, text="", font=("Segoe UI", 12),
                                      fg="#ff4444", bg="black")
        self._error_label.pack(pady=(10, 0))

        w.bind("<Return>", lambda e: self._try_unlock())

    def show(self):
        self._visible = True
        self._pw_entry.delete(0, tk.END)
        self._error_label.config(text="")
        w = self._win
        w.geometry(f"{w.winfo_screenwidth()}x{w.winfo_screenheight()}+0+0")
        w.deiconify()
        w.lift()
        w.focus_force()
        w.grab_set()
        self._pw_entry.focus_set()
        self._countdown_remaining = self._auto_unlock_secs
        self._tick()

    def hide(self):
        self._visible = False
        if self._countdown_job:
            self._win.after_cancel(self._countdown_job)
            self._countdown_job = None
        self._win.grab_release()
        self._win.withdraw()

    def _tick(self):
        if not self._visible:
            return
        mins, secs = divmod(self._countdown_remaining, 60)
        self._countdown_label.config(text=f"Unlocking in {mins:02d}:{secs:02d}")
        if self._countdown_remaining <= 0:
            self.hide()
            self._on_auto_unlock()
            return
        self._countdown_remaining -= 1
        self._countdown_job = self._win.after(1000, self._tick)

    def _try_unlock(self):
        password = self._pw_entry.get()
        if self._on_password_unlock(password):
            self.hide()
        else:
            self._error_label.config(text="Incorrect password")
            self._pw_entry.delete(0, tk.END)
