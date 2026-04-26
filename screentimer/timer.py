import threading


class TimerThread(threading.Thread):
    """Drives the lock/unlock cycle. Uses seconds internally for testability;
    SettingsWindow passes lock_interval_secs = minutes * 60."""

    def __init__(self, lock_interval_secs: float, auto_unlock_secs: float,
                 on_lock, on_unlock):
        super().__init__(daemon=True)
        self._lock_interval = lock_interval_secs
        self._auto_unlock = auto_unlock_secs
        self._on_lock = on_lock
        self._on_unlock = on_unlock
        self._stop_event = threading.Event()
        self._manual_unlock_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            # Wait X seconds (lock interval), or until stopped
            if self._stop_event.wait(timeout=self._lock_interval):
                break

            self._on_lock()

            # Wait Y seconds (auto-unlock) or until manual unlock or stop
            self._manual_unlock_event.clear()
            unlock_trigger = threading.Event()

            def auto():
                if not self._stop_event.wait(timeout=self._auto_unlock):
                    unlock_trigger.set()

            auto_thread = threading.Thread(target=auto, daemon=True)
            auto_thread.start()

            # Block until either auto-unlock fires or manual unlock or stop
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
