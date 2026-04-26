import tkinter as tk
from screentimer.config import ConfigStore
from screentimer.settings import SettingsWindow
from screentimer.overlay import LockOverlay
from screentimer.countdown import CountdownWidget
from screentimer.timer import TimerThread


def main():
    root = tk.Tk()
    root.withdraw()  # hidden root window; all UI lives in Toplevels

    store = ConfigStore()
    timer: list[TimerThread] = []
    overlay: list[LockOverlay] = []

    settings_win = tk.Toplevel(root)
    countdown: list[CountdownWidget] = []

    def start_timer(cfg):
        # Stop any existing timer
        if timer:
            timer[0].stop()
            timer.clear()

        auto_secs = cfg.auto_unlock_mins * 60
        daily_secs = cfg.daily_limit_mins * 60
        initial_used = store.load_daily_used_secs()

        # Create or update overlay
        if not overlay:
            ov = LockOverlay(
                root=root,
                auto_unlock_secs=auto_secs,
                on_password_unlock=lambda pw: cfg.check_password(pw),
                on_auto_unlock=lambda: _manual_unlock(),
            )
            overlay.append(ov)
        else:
            overlay[0].update_config(auto_secs, lambda pw: cfg.check_password(pw))

        def _manual_unlock():
            if timer:
                timer[0].manual_unlock()

        def on_lock():
            root.after(0, lambda: [
                overlay[0].show(),
                countdown[0].set_locked() if countdown else None,
            ])

        def on_tick(remaining, used):
            store.save_daily_used_secs(int(used))
            if countdown:
                root.after(0, lambda r=remaining, u=used: countdown[0].update_tick(r, u, daily_secs))

        def on_daily_limit():
            store.save_daily_used_secs(int(timer[0].used_secs if timer else daily_secs))
            root.after(0, lambda: [
                overlay[0].show_daily_limit(),
                countdown[0].set_daily_limit_reached() if countdown else None,
            ])

        t = TimerThread(
            lock_interval_secs=cfg.lock_interval_mins * 60,
            auto_unlock_secs=auto_secs,
            on_lock=on_lock,
            on_unlock=lambda: None,  # auto-unlock handled by LockOverlay._tick
            on_tick=on_tick,
            daily_limit_secs=daily_secs,
            initial_used_secs=initial_used,
            on_daily_limit=on_daily_limit,
        )
        timer.append(t)
        t.start()

        # Show countdown widget on first start
        if not countdown:
            cw = CountdownWidget(root=root, on_open_settings=lambda: sw.show_for_running())
            countdown.append(cw)
        # Pre-populate with initial state
        countdown[0].update_tick(cfg.lock_interval_mins * 60, initial_used, daily_secs)

    sw = SettingsWindow(root=settings_win, store=store, on_start=start_timer, on_apply=start_timer)

    root.mainloop()


if __name__ == "__main__":
    main()
