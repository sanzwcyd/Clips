# Clips

Clipboard manager for Windows: searchable history, pinned items, global hotkey,
frosted-glass UI, accent colour that follows Windows, English/Indonesian (auto).

## Run from source (Windows 10/11)

```
pip install -r requirements.txt
python main.py
```

Clips lives in the system tray. Default hotkey: **Ctrl+Shift+V**
(change it in Settings). Data is stored in `%APPDATA%\Clips`.

## Build the .exe

Double-click `build.bat` (needs Python + pip). Output: `dist\Clips.exe`.

## Quitting Clips

Right-click the tray icon -> **Quit**, or Settings -> **Quit Clips**. If you can't see the tray icon,
click the ^ arrow next to the clock (or drag the icon out of the overflow area).
Launching Clips again while it is running just opens the history popup.

## Make an installer (Inno Setup)

1. Run `build.bat` (creates `dist\Clips.exe`).
2. Open `installer\Clips.iss` in Inno Setup and press Ctrl+F9.
3. Your installer is created in `installer_output\`.

The installer installs per-user (no admin prompt), adds a Start menu shortcut (optional desktop
shortcut), closes a running Clips before updating/uninstalling, and offers to delete history/settings
when uninstalling.

## Features in this version (0.1.3)

- History of text and images (SQLite), search, tabs, pin, delete, Enter to paste
- Global hotkey, tray menu (open, pause, clear, run at startup, settings, about, quit)
- Eased animations (ease-out in, ease-in out, ease-in-out for moves/toggles);
  respects Windows' "show animations" setting
- Language: follows the Windows display language (Indonesian -> id, otherwise en),
  switchable from the globe button or Settings
- Settings window with About + current version
- Detection of emails/passwords (off by default): floating button near the taskbar,
  "Detected items" window, passwords encrypted with Windows DPAPI, masked, auto-deleted
- Ignored apps list (nothing is recorded from them)

## Things to set / verify on your own PC

- Your profile links are set in `clips/about.py` -> `LINKS`.
- Glass look: each window takes a snapshot of the screen behind it, blurs and darkens it. It is
  always blurred (Windows' own acrylic turns see-through on inactive windows), but it is a still
  picture taken when the window opens, not a live blur. Only the tray menu still uses native acrylic.
- Password detection relies mainly on the "ExcludeClipboardContentFromMonitorProcessing"
  clipboard format that password managers set; the character-based guess is only a fallback.
- Auto-paste sends Ctrl+V to the window that was active when the hotkey was pressed.

## Layout

```
main.py              entry point
clips/app.py         wires everything together (clipboard, hotkey, windows)
clips/popup.py       history popup        clips/settings_window.py  Settings
clips/detected.py    Detected items + floating button
clips/about.py       About / credit (Clawd)   clips/tray.py  tray menu
clips/winutil.py     all Windows-specific code    clips/hotkey.py  global hotkey
clips/db.py          SQLite storage       clips/detect.py  email/password detection
clips/i18n.py        English / Indonesian strings  clips/theme.py  look, icons, easing
```
