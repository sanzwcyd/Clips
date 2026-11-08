<p align="center">
  <img src="assets/icon.png" width="96" alt="Clips logo">
</p>

<h1 align="center">Clips</h1>
<p align="center">A fast, good-looking clipboard manager for Windows.<br>
Searchable history · pinned items · global hotkey · frosted-glass UI · English / Bahasa Indonesia</p>

---

## Features

- **History** of everything you copy: text, emails and images, stored locally in SQLite
- **Instant search**, filter tabs (All / Text / Images / Pinned) and **pin** the items you reuse
- **Global hotkey** (default `Ctrl+Shift+V`, changeable) opens the history; `Enter` pastes into the app you were using
- **Keyboard friendly**: `↑ ↓` select, `Enter` paste, `Del` delete, `Esc` close
- **Frosted-glass look** with smooth, eased animations (respects Windows' "show animations" setting)
- **Accent colour follows Windows** (red accent on Windows → red in Clips, default blue → blue)
- **Language follows Windows**: Indonesian Windows → Indonesian app, anything else → English. Switch any time with the 🌐 button or in Settings
- **Email / password detection** (off by default): a small floating button appears near the taskbar when an email or password is copied, with a *Detected items* window
- **Ignored apps**: nothing is recorded from the apps you list (for example your password manager)
- Lives in the **system tray**; optional **run at Windows startup**

## Download

Grab one of these from the [Releases](../../releases) page:

| File | For |
| --- | --- |
| `Clips-Setup-v1.0.0.exe` | Normal install (Start menu shortcut, clean uninstall) |
| `Clips-v1.0.0-portable.zip` | No install: unzip and run `Clips.exe` |
| `Clips-v1.0.0-source.zip` | Source code, to read or build yourself |

> Windows may warn "Windows protected your PC" because the app isn't code-signed.
> Click **More info → Run anyway**.

## Using Clips

1. Start Clips. An icon appears in the system tray (click the **^** arrow next to the clock if you can't see it).
2. Copy things as usual.
3. Press **Ctrl+Shift+V**, pick an item, press **Enter**. It is pasted into the window you were in.
4. Click the ⚙ icon for **Settings**. **About** and the current version are at the bottom.
5. To quit: right-click the tray icon → **Quit**, or **Settings → Quit Clips**.

Launching Clips again while it is already running just opens the history popup.

### Settings

| Section | Options |
| --- | --- |
| General | Language · Run at Windows startup · Accent colour follows Windows |
| History | Keep up to N items · Save images · Clear history on exit |
| Shortcut & privacy | Change hotkey · Detect emails & passwords · Show detection button (Always / Only passwords / Never) · Button position · Ignored apps |

## Privacy

- Everything stays on your PC in `%APPDATA%\Clips`. Clips never connects to the internet.
- The normal history (text, emails, images) is stored **unencrypted** in a local SQLite file. Use *Ignored apps* and *Pause recording* for anything sensitive, and *Clear history on exit* if you share the PC.
- Content that password managers mark as private (the `ExcludeClipboardContentFromMonitorProcessing` clipboard format) is **never** recorded, unless you turn on *Detect emails & passwords*.
- With detection on, passwords are encrypted with **Windows DPAPI**, shown masked (••••), and **deleted automatically** after a few minutes.
- Detecting a password by looking at the text is a guess (passwords have no fixed format) and can be wrong. The clipboard flag from password managers is the reliable signal.

## Run from source

Requires Windows 10/11 and Python 3.10+ (3.12 recommended).

```bash
pip install -r requirements.txt
python main.py
```

## Build

```bash
build.bat          # creates dist\Clips.exe (PyInstaller)
make_release.bat   # builds the exe and creates the portable + source zips in .\release\
```

For the installer: run `build.bat`, open `installer\Clips.iss` in [Inno Setup](https://jrsoftware.org/isinfo.php) and press **Ctrl+F9**. The installer is created in `installer_output\`.

## Project layout

```
main.py                    entry point
clips/app.py               wires everything together (clipboard, hotkey, windows)
clips/popup.py             history popup
clips/settings_window.py   Settings window
clips/detected.py          Detected items window + floating button
clips/about.py             About / credits
clips/tray.py              tray icon and menu
clips/winutil.py           all Windows-specific code (accent colour, startup, DPAPI, …)
clips/hotkey.py            global hotkey
clips/db.py                SQLite storage
clips/detect.py            email / password detection
clips/i18n.py              English / Indonesian strings
clips/theme.py             look & feel, icons, easing curves
installer/Clips.iss        Inno Setup script
```

Built with Python and [PySide6](https://doc.qt.io/qtforpython-6/) (Qt).

## Known limitations

- Windows only.
- The glass effect is a blurred snapshot of what is behind a window, taken when it opens. It isn't a live blur.
- Auto-paste sends `Ctrl+V` to the window that was active when you pressed the hotkey. A few apps that block simulated keystrokes may need a manual paste.

## Credits

Made by **sanz & clawd**

[Instagram](https://www.instagram.com/sanz.arw/) · [X](https://x.com/LineBezier) · [GitHub](https://github.com/sanzwcyd) · [Saweria](https://saweria.co/sanzwcyd)



## Bahasa Indonesia (ringkas)

**Clips** adalah clipboard manager untuk Windows: riwayat copy-paste yang bisa dicari, item bisa disematkan, hotkey global (`Ctrl+Shift+V`), tampilan kaca buram dengan animasi halus, warna aksen mengikuti Windows, dan bahasa otomatis mengikuti Windows (Indonesia atau Inggris).

- **Pakai**: jalankan Clips → ikon muncul di system tray → salin seperti biasa → tekan `Ctrl+Shift+V` → pilih item → `Enter` untuk menempel.
- **Keluar**: klik kanan ikon tray → **Quit**, atau **Settings → Quit Clips**.
- **Install**: pakai `Clips-Setup-x.y.z.exe`, atau `Clips-x.y.z-portable.zip` tanpa install.
- **Privasi**: semua data tersimpan lokal di `%APPDATA%\Clips`. Riwayat biasa disimpan tanpa enkripsi, jadi gunakan *Ignored apps* atau *Pause recording* untuk hal sensitif. Password (jika deteksi dinyalakan) dienkripsi dan dihapus otomatis.
