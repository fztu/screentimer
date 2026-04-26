# ScreenTimer — Design Spec
_Date: 2026-04-26_

## Overview

A standalone Windows 11 `.exe` (no runtime required) that enforces periodic screen breaks for children. Every X minutes a fullscreen lock overlay appears. A parent can dismiss it with a password, or it auto-dismisses after Y minutes. Both X and Y are set via a small settings UI at launch.

## Architecture

Single Python 3 file compiled to a standalone `.exe` with PyInstaller.

Two logical layers:
- **Settings UI** — tkinter window shown at startup for configuration and launch
- **Lock Overlay** — fullscreen tkinter window shown on a timer

A background daemon thread drives the lock/unlock cycle.

## Components

### 1. Settings UI (`SettingsWindow`)

Shown when the app starts. Contains:
- **Lock interval (X)** — spinbox, minutes, default 30
- **Auto-unlock delay (Y)** — spinbox, minutes, default 5
- **Parent password** — password entry field
- **Start** button — validates inputs, saves config, hides the settings window, starts the background timer thread

The settings window minimizes to the taskbar after Start. It does not provide a tray icon (keeps scope simple).

### 2. Lock Overlay (`LockOverlay`)

A fullscreen, borderless, always-on-top black tkinter window. Shown when the X-minute timer fires.

Contents:
- Title text: "Time for a break!"
- Auto-unlock countdown: "Unlocking in MM:SS"
- Password field + "Unlock" button for parent early unlock
- Wrong password shows a brief "Incorrect password" label

Hardening (reasonable for Option B — custom overlay):
- `overrideredirect(True)` removes title bar / close button
- `attributes('-topmost', True)` keeps it above all windows
- Alt+F4 and WM_DELETE_WINDOW are intercepted and suppressed
- Grab set on the overlay to capture keyboard/mouse focus

Limitation: Task Manager can still kill the process. This is the accepted trade-off.

### 3. Timer Thread (`TimerThread`)

A daemon thread that runs independently of the UI. Responsibilities:
- Counts down X minutes, then signals the main thread to show the overlay
- Once the overlay is shown, counts down Y minutes, then signals auto-unlock
- On either manual or auto unlock, resets and restarts the X countdown
- Uses `threading.Event` for signalling between thread and UI

### 4. Configuration (`AppConfig`)

A simple dataclass holding:
- `lock_interval_mins: int` — X
- `auto_unlock_mins: int` — Y
- `password_hash: str` — SHA-256 hash of the parent password (never stored plaintext)

### 5. Config Persistence (`ConfigStore`)

Settings are saved to and loaded from `%APPDATA%\ScreenTimer\config.json` as JSON:

```json
{
  "lock_interval_mins": 30,
  "auto_unlock_mins": 5,
  "password_hash": "<sha256 hex digest>"
}
```

Behaviour:
- On launch, if the file exists, pre-fill the Settings UI fields (X, Y). The password field is left blank — the parent must re-enter it to confirm they know it, but the stored hash is used for validation if they leave it blank and click Start (i.e. keep existing password).
- On "Start", write updated values back to the file.
- The directory is created if it does not exist.
- Password is hashed with SHA-256 before storage and comparison. No salt needed given the low-stakes local use case (bcrypt would be overkill and adds a dependency).

## Data Flow

```
[SettingsWindow] --start--> [AppConfig] --> [TimerThread]
                                                  |
                              X mins elapsed       |
                                  ↓               |
                          [LockOverlay shown]      |
                                  |               |
               parent unlocks     |   Y mins elapsed
                  ↓               |       ↓
             overlay hidden <-----+------ overlay hidden
                  |
             TimerThread resets X countdown
```

## Build & Distribution

- Developed with Python 3.11+
- Dependencies: only stdlib (tkinter, hashlib, json, pathlib all included)
- Build command: `pyinstaller --onefile --windowed screentimer.py`
- Output: `dist/screentimer.exe` — single file, no installer needed
- A `build.bat` helper script is included for convenience

## Out of Scope

- System tray icon
- Multiple user profiles
- Scheduled daily limits (total screen time per day)
- Windows lock screen integration
