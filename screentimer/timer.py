import threading


class TimerThread(threading.Thread):
    """Drives the lock/unlock cycle. Uses seconds internally for testability;
    SettingsWindow passes lock_interval_secs = minutes * 60."""

    def __init__(self, lock_interval_secs: float, auto_unlock_secs: float,
                 on_lock, on_unlock, on_tick=None,
                 daily_limit_secs: float = 0, initial_used_secs: float = 0,
                 on_daily_limit=None):
        super().__init__(daemon=True)
        self._lock_interval = lock_interval_secs
        self._auto_unlock = auto_unlock_secs
        self._on_lock = on_lock
        self._on_unlock = on_unlock
        self._on_tick = on_tick          # called each active second: (remaining_secs, used_secs)
        self._daily_limit = daily_limit_secs
        self._used_secs = initial_used_secs
        self._on_daily_limit = on_daily_limit
        self._stop_event = threading.Event()
        self._manual_unlock_event = threading.Event()

    @property
    def used_secs(self) -> float:
        return self._used_secs

    def run(self):
        while not self._stop_event.is_set():
            elapsed = 0.0
            daily_hit = False

            # Active period: count down until next scheduled lock
            while elapsed < self._lock_interval and not self._stop_event.is_set():
                tick = min(1.0, self._lock_interval - elapsed)
                if self._stop_event.wait(timeout=tick):
                    return
                elapsed += tick
                self._used_secs += tick
                remaining = self._lock_interval - elapsed
                if self._on_tick:
                    self._on_tick(remaining, self._used_secs)
                if self._daily_limit > 0 and self._used_secs >= self._daily_limit:
                    daily_hit = True
                    break

            if self._stop_event.is_set():
                break

            self._on_lock()

            if daily_hit:
                if self._on_daily_limit:
                    self._on_daily_limit()
                # Block until explicitly stopped — daily limit reached, no auto-unlock
                self._stop_event.wait()
                return

            # Wait for auto-unlock or manual unlock
            self._manual_unlock_event.clear()
            unlock_trigger = threading.Event()

            def auto():
                if not self._stop_event.wait(timeout=self._auto_unlock):
                    unlock_trigger.set()

            threading.Thread(target=auto, daemon=True).start()

            while not self._stop_event.is_set():
                if unlock_trigger.is_set() or self._manual_unlock_event.is_set():
                    break
                self._stop_event.wait(timeout=0.05)

            if self._stop_event.is_set():
                break

            self._on_unlock()

    def manual_unlock(self):
        self._manual_unlock_event.set()

    def stop(self):
        self._stop_event.set()
        self._manual_unlock_event.set()
