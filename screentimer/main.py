import tkinter as tk
from screentimer.config import ConfigStore
from screentimer.settings import SettingsWindow
from screentimer.overlay import LockOverlay
from screentimer.timer import TimerThread


def main():
    root = tk.Tk()
    root.withdraw()  # hidden root window; SettingsWindow and LockOverlay are Toplevels

    store = ConfigStore()
    timer: list[TimerThread] = []  # mutable container so callbacks can reference it

    # Re-show SettingsWindow is out of scope; root stays hidden after Start
    settings_win = tk.Toplevel(root)
    overlay: list[LockOverlay] = []

    def on_start(cfg):
        auto_secs = cfg.auto_unlock_mins * 60

        ov = LockOverlay(
            root=root,
            auto_unlock_secs=auto_secs,
            on_password_unlock=lambda pw: cfg.check_password(pw),
            on_auto_unlock=lambda: on_unlock(),
        )
        overlay.append(ov)

        def on_lock():
            root.after(0, ov.show)

        def on_unlock():
            if timer:
                timer[0].manual_unlock()

        t = TimerThread(
            lock_interval_secs=cfg.lock_interval_mins * 60,
            auto_unlock_secs=auto_secs,
            on_lock=on_lock,
            on_unlock=lambda: None,  # auto-unlock path handled by LockOverlay._tick
        )
        timer.append(t)
        t.start()

    sw = SettingsWindow(root=settings_win, store=store, on_start=on_start)

    root.mainloop()


if __name__ == "__main__":
    main()
