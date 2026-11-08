"""All Windows-specific code lives here. Every function degrades to a no-op
on other platforms so the UI can still be developed/tested anywhere."""
import base64
import os
import sys
import time

IS_WIN = sys.platform == "win32"

if IS_WIN:
    import ctypes
    import winreg
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetUserDefaultUILanguage.restype = wintypes.WORD
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]

    class _AccentPolicy(ctypes.Structure):
        _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

    class _WCAData(ctypes.Structure):
        _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t)]

    user32.SetWindowCompositionAttribute.argtypes = [wintypes.HWND, ctypes.POINTER(_WCAData)]

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "Clips"


# ---------------------------------------------------------------- language
def ui_language_code() -> str:
    """'id' when Windows' display language is Indonesian, otherwise 'en'."""
    if IS_WIN:
        try:
            return "id" if (kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x21 else "en"
        except Exception:
            pass
    lang = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "").lower()
    return "id" if lang.startswith("id") else "en"


# ------------------------------------------------------------------ system
def accent_color(default: str = "#0078D4") -> str:
    if IS_WIN:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM") as k:
                v, _ = winreg.QueryValueEx(k, "AccentColor")  # 0xAABBGGRR
            return "#{:02X}{:02X}{:02X}".format(v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF)
        except OSError:
            pass
    return default


def animations_enabled() -> bool:
    if IS_WIN:
        try:
            flag = wintypes.BOOL()
            if user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(flag), 0):  # CLIENTAREAANIMATION
                return bool(flag.value)
        except Exception:
            pass
    return True


def apply_acrylic(hwnd: int, tint=(22, 23, 30, 120)) -> bool:
    """Acrylic blur-behind via SetWindowCompositionAttribute + round corners on Win11."""
    if not IS_WIN:
        return False
    try:
        r, g, b, a = tint
        policy = _AccentPolicy(4, 2, (a << 24) | (b << 16) | (g << 8) | r, 0)  # ACRYLICBLURBEHIND
        data = _WCAData(19, ctypes.cast(ctypes.byref(policy), ctypes.c_void_p), ctypes.sizeof(policy))
        ok = bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data)))
        try:  # Windows 11: rounded corners (ignored on Windows 10)
            pref = ctypes.c_int(2)
            dwmapi.DwmSetWindowAttribute(wintypes.HWND(hwnd), 33, ctypes.byref(pref), 4)
        except Exception:
            pass
        return ok
    except Exception:
        return False


# ----------------------------------------------------------------- startup
def _startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --background'
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    main = os.path.abspath(sys.argv[0])
    return f'"{pyw}" "{main}" --background'


def set_run_at_startup(enabled: bool) -> None:
    if not IS_WIN:
        return
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, _startup_command())
            else:
                try:
                    winreg.DeleteValue(k, RUN_NAME)
                except FileNotFoundError:
                    pass
    except OSError:
        pass


# -------------------------------------------------------- windows & input
def foreground_window() -> int:
    return int(user32.GetForegroundWindow() or 0) if IS_WIN else 0


def process_name_of(hwnd: int) -> str:
    """Lower-case exe name (e.g. 'keepass.exe') of the process owning hwnd."""
    if not IS_WIN or not hwnd:
        return ""
    try:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        h = kernel32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(520)
            size = wintypes.DWORD(520)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(h)
    except Exception:
        pass
    return ""


def force_foreground(hwnd: int) -> None:
    """Reliably bring our window to the front after a global hotkey."""
    if not IS_WIN or not hwnd:
        return
    try:
        fg = user32.GetForegroundWindow()
        cur = kernel32.GetCurrentThreadId()
        fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
        if fg_tid and fg_tid != cur:
            user32.AttachThreadInput(cur, fg_tid, True)
        user32.BringWindowToTop(wintypes.HWND(hwnd))
        user32.SetForegroundWindow(wintypes.HWND(hwnd))
        if fg_tid and fg_tid != cur:
            user32.AttachThreadInput(cur, fg_tid, False)
    except Exception:
        pass


def paste_into(hwnd: int) -> None:
    """Give focus back to hwnd and send Ctrl+V."""
    if not IS_WIN:
        return
    try:
        if hwnd:
            user32.SetForegroundWindow(wintypes.HWND(hwnd))
        time.sleep(0.06)
        for vk in (0x10, 0x12, 0x5B):  # release Shift/Alt/Win if still held from the hotkey
            user32.keybd_event(vk, 0, 2, 0)
        user32.keybd_event(0x11, 0, 0, 0)
        user32.keybd_event(0x56, 0, 0, 0)
        user32.keybd_event(0x56, 0, 2, 0)
        user32.keybd_event(0x11, 0, 2, 0)
    except Exception:
        pass


_exclude_fmt = None


def clipboard_is_sensitive() -> bool:
    """True when the app that copied asked clipboard managers to ignore it
    (password managers set this format)."""
    global _exclude_fmt
    if not IS_WIN:
        return False
    try:
        if _exclude_fmt is None:
            _exclude_fmt = user32.RegisterClipboardFormatW("ExcludeClipboardContentFromMonitorProcessing")
        return bool(user32.IsClipboardFormatAvailable(_exclude_fmt))
    except Exception:
        return False


# -------------------------------------------------------------------- DPAPI
def protect(data: bytes) -> bytes:
    if not IS_WIN:
        return b"plain:" + data  # development fallback only
    buf = ctypes.create_string_buffer(data, len(data))
    inb = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = _Blob()
    if not crypt32.CryptProtectData(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))


def unprotect(data: bytes) -> bytes:
    if not IS_WIN:
        return data[len(b"plain:"):] if data.startswith(b"plain:") else data
    buf = ctypes.create_string_buffer(data, len(data))
    inb = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = _Blob()
    if not crypt32.CryptUnprotectData(ctypes.byref(inb), None, None, None, None, 0, ctypes.byref(out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))


def encrypt_text(text: str) -> str:
    return base64.b64encode(protect(text.encode("utf-8"))).decode("ascii")


def decrypt_text(token: str) -> str:
    try:
        return unprotect(base64.b64decode(token)).decode("utf-8")
    except Exception:
        return ""
