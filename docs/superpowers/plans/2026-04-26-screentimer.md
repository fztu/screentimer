# ScreenTimer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Windows 11 `.exe` that locks a child's screen on a timer, with parent password unlock and auto-unlock after a configurable delay.

**Architecture:** A single Python entry point (`main.py`) wires together four modules: `config.py` (dataclass + JSON persistence), `timer.py` (background daemon thread), `overlay.py` (fullscreen tkinter lock screen), and `settings.py` (startup configuration UI). PyInstaller bundles everything into one `.exe` with no runtime required.

**Tech Stack:** Python 3.11+, tkinter (stdlib), hashlib (stdlib), PyInstaller (dev dependency)

---

## File Map

| File | Responsibility |
|------|---------------|
| `screentimer/config.py` | `AppConfig` dataclass + `ConfigStore` (load/save JSON, hash password) |
| `screentimer/timer.py` | `TimerThread` — daemon thread driving lock/unlock cycle |
| `screentimer/overlay.py` | `LockOverlay` — fullscreen always-on-top tkinter window |
| `screentimer/settings.py` | `SettingsWindow` — startup config UI |
| `screentimer/main.py` | Entry point — instantiates and wires all components |
| `screentimer/__init__.py` | Empty package marker |
| `tests/test_config.py` | Unit tests for `AppConfig` and `ConfigStore` |
| `tests/test_timer.py` | Unit tests for `TimerThread` logic |
| `build.bat` | One-click PyInstaller build script |
| `requirements-dev.txt` | `pytest` for running tests |

---

## Task 1: Project Scaffold

**Files:**
- Create: `screentimer/__init__.py`
- Create: `requirements-dev.txt`
- Create: `build.bat`

- [ ] **Step 1: Create the package directory and empty init**

```bash
mkdir screentimer
```

Create `screentimer/__init__.py` — empty file:
```python
```

- [ ] **Step 2: Create `requirements-dev.txt`**

```
pytest
pyinstaller
```

- [ ] **Step 3: Create `build.bat`**

```bat
@echo off
pyinstaller --onefile --windowed --name screentimer screentimer/main.py
echo.
echo Build complete: dist\screentimer.exe
pause
```

- [ ] **Step 4: Install dev dependencies**

Run:
```bash
pip install -r requirements-dev.txt
```

Expected: installs pytest and pyinstaller without errors.

- [ ] **Step 5: Commit**

```bash
git init
git add screentimer/__init__.py requirements-dev.txt build.bat
git commit -m "chore: project scaffold"
```

---

## Task 2: AppConfig and ConfigStore

**Files:**
- Create: `screentimer/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/__init__.py` — empty file.

Create `tests/test_config.py`:

```python
import hashlib
import json
import os
from pathlib import Path
import pytest
from screentimer.config import AppConfig, ConfigStore, hash_password


def test_hash_password_returns_sha256_hex():
    result = hash_password("secret")
    expected = hashlib.sha256("secret".encode()).hexdigest()
    assert result == expected


def test_hash_password_empty_string():
    result = hash_password("")
    assert result == hashlib.sha256(b"").hexdigest()


def test_appconfig_defaults():
    cfg = AppConfig(lock_interval_mins=30, auto_unlock_mins=5, password_hash="abc")
    assert cfg.lock_interval_mins == 30
    assert cfg.auto_unlock_mins == 5
    assert cfg.password_hash == "abc"


def test_appconfig_check_password_correct():
    h = hash_password("mypassword")
    cfg = AppConfig(lock_interval_mins=10, auto_unlock_mins=2, password_hash=h)
    assert cfg.check_password("mypassword") is True


def test_appconfig_check_password_wrong():
    h = hash_password("mypassword")
    cfg = AppConfig(lock_interval_mins=10, auto_unlock_mins=2, password_hash=h)
    assert cfg.check_password("wrong") is False


def test_configstore_save_and_load(tmp_path):
    store = ConfigStore(config_dir=tmp_path)
    cfg = AppConfig(lock_interval_mins=20, auto_unlock_mins=3, password_hash=hash_password("pw"))
    store.save(cfg)

    loaded = store.load()
    assert loaded is not None
    assert loaded.lock_interval_mins == 20
    assert loaded.auto_unlock_mins == 3
    assert loaded.password_hash == hash_password("pw")


def test_configstore_load_returns_none_when_missing(tmp_path):
    store = ConfigStore(config_dir=tmp_path)
    assert store.load() is None


def test_configstore_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b"
    store = ConfigStore(config_dir=nested)
    cfg = AppConfig(lock_interval_mins=5, auto_unlock_mins=1, password_hash="x")
    store.save(cfg)
    assert (nested / "config.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `screentimer.config` does not exist yet.

- [ ] **Step 3: Implement `screentimer/config.py`**

```python
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@dataclass
class AppConfig:
    lock_interval_mins: int
    auto_unlock_mins: int
    password_hash: str

    def check_password(self, password: str) -> bool:
        return hash_password(password) == self.password_hash


class ConfigStore:
    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            appdata = Path(os.environ.get("APPDATA", Path.home()))
            config_dir = appdata / "ScreenTimer"
        self._path = Path(config_dir) / "config.json"

    def load(self) -> AppConfig | None:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return AppConfig(
            lock_interval_mins=data["lock_interval_mins"],
            auto_unlock_mins=data["auto_unlock_mins"],
            password_hash=data["password_hash"],
        )

    def save(self, config: AppConfig) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({
                "lock_interval_mins": config.lock_interval_mins,
                "auto_unlock_mins": config.auto_unlock_mins,
                "password_hash": config.password_hash,
            }, indent=2),
            encoding="utf-8",
        )
```

Note: add `import os` at the top of the file (missing from the snippet above — add it after `import hashlib`).

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add screentimer/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: AppConfig dataclass and ConfigStore with JSON persistence"
```

---

## Task 3: TimerThread

**Files:**
- Create: `screentimer/timer.py`
- Create: `tests/test_timer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_timer.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_timer.py -v
```

Expected: `ImportError` — `screentimer.timer` does not exist yet.

- [ ] **Step 3: Implement `screentimer/timer.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_timer.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all 11 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add screentimer/timer.py tests/test_timer.py
git commit -m "feat: TimerThread driving lock/unlock cycle"
```

---

## Task 4: LockOverlay

**Files:**
- Create: `screentimer/overlay.py`

No automated tests — tkinter windows cannot be unit-tested headlessly. Manual smoke test described at end.

- [ ] **Step 1: Implement `screentimer/overlay.py`**

```python
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
```

- [ ] **Step 2: Manual smoke test (skip if no display available)**

Run `python screentimer/main.py` after Task 6 is complete (main.py wires everything together). Verify:
- Overlay covers full screen with black background
- Countdown counts down from Y minutes
- Correct password dismisses overlay
- Wrong password shows "Incorrect password" in red
- Alt+F4 does not close the overlay
- After overlay dismisses, X-minute timer restarts

- [ ] **Step 3: Commit**

```bash
git add screentimer/overlay.py
git commit -m "feat: LockOverlay fullscreen tkinter window"
```

---

## Task 5: SettingsWindow

**Files:**
- Create: `screentimer/settings.py`

- [ ] **Step 1: Implement `screentimer/settings.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add screentimer/settings.py
git commit -m "feat: SettingsWindow startup configuration UI"
```

---

## Task 6: Main Entry Point

**Files:**
- Create: `screentimer/main.py`

- [ ] **Step 1: Implement `screentimer/main.py`**

```python
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
```

- [ ] **Step 2: Run the app manually**

```bash
python screentimer/main.py
```

Expected: Settings window appears. Fill in values, click Start. Window hides. After X minutes (set low, e.g. 1, for testing) the black overlay appears. Verify countdown, correct password dismisses it, wrong password shows error, overlay auto-dismisses after Y minutes.

- [ ] **Step 3: Run the full test suite one more time**

```bash
pytest -v
```

Expected: all 11 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add screentimer/main.py
git commit -m "feat: main entry point wiring all components"
```

---

## Task 7: Build the Standalone .exe

**Files:**
- `build.bat` (already created in Task 1)

- [ ] **Step 1: Run the build**

On a Windows machine (or Windows-targeted build environment):

```bat
build.bat
```

Or directly:

```bash
pyinstaller --onefile --windowed --name screentimer screentimer/main.py
```

Expected output ends with:
```
Building EXE from EXE-00.toc completed successfully.
Build complete: dist\screentimer.exe
```

- [ ] **Step 2: Test the .exe**

Double-click `dist\screentimer.exe`. Verify:
- Settings window opens with no Python runtime installed
- All behaviour from Task 6 Step 2 manual test works identically
- Config is saved to `%APPDATA%\ScreenTimer\config.json` after clicking Start
- Re-launching the `.exe` pre-fills the saved X and Y values

- [ ] **Step 3: Commit**

```bash
git add dist/screentimer.exe
git commit -m "build: add compiled screentimer.exe"
```

> Note: add `dist/` and `build/` and `*.spec` to `.gitignore` if you prefer not to commit the binary.

---

## Self-Review Notes

- **Spec coverage:** All 5 spec components covered (SettingsWindow ✓, LockOverlay ✓, TimerThread ✓, AppConfig ✓, ConfigStore ✓). Build + distribution covered in Task 7.
- **Password keep-existing flow:** Covered in `SettingsWindow._on_start_click` — blank field + `_saved_hash` present → reuse hash.
- **Alt+F4 suppression:** Covered in `LockOverlay._build_ui`.
- **Auto-unlock in LockOverlay vs TimerThread:** `LockOverlay._tick` drives the visual countdown and calls `on_auto_unlock`. `TimerThread.manual_unlock()` is called on parent password unlock so the thread resets its X countdown. The `on_unlock` callback in `TimerThread` is a no-op because `LockOverlay` owns the auto-unlock path — no double-fire.
- **No placeholder steps detected.**
- **Type consistency:** `AppConfig`, `ConfigStore`, `hash_password`, `TimerThread`, `LockOverlay`, `SettingsWindow` all consistent across tasks.
