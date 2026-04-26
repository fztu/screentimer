import threading
import time
import pytest
from screentimer.timer import TimerThread


def test_timer_fires_lock_callback_after_interval():
    locked = threading.Event()
    t = TimerThread(lock_interval_secs=0.05, auto_unlock_secs=10, on_lock=locked.set, on_unlock=lambda: None)
    t.start()
    assert locked.wait(timeout=1.0), "on_lock callback was not called within 1 second"
    t.stop()


def test_timer_fires_auto_unlock_after_auto_unlock_interval():
    unlocked = threading.Event()
    t = TimerThread(lock_interval_secs=0.05, auto_unlock_secs=0.05, on_lock=lambda: None, on_unlock=unlocked.set)
    t.start()
    assert unlocked.wait(timeout=1.0), "on_unlock callback was not called within 1 second"
    t.stop()


def test_timer_resets_after_manual_unlock():
    lock_count = {"n": 0}
    lock_event = threading.Event()

    def on_lock():
        lock_count["n"] += 1
        lock_event.set()

    t = TimerThread(lock_interval_secs=0.05, auto_unlock_secs=10, on_lock=on_lock, on_unlock=lambda: None)
    t.start()
    assert lock_event.wait(timeout=1.0)
    lock_event.clear()

    t.manual_unlock()
    assert lock_event.wait(timeout=1.0), "timer did not re-lock after manual unlock"
    assert lock_count["n"] >= 2
    t.stop()


def test_timer_stop_halts_thread():
    t = TimerThread(lock_interval_secs=10, auto_unlock_secs=10, on_lock=lambda: None, on_unlock=lambda: None)
    t.start()
    t.stop()
    t.join(timeout=1.0)
    assert not t.is_alive()
