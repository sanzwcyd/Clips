"""Global hotkey through RegisterHotKey + a Qt native event filter."""
from PySide6.QtCore import QAbstractNativeEventFilter, Qt

from . import winutil

if winutil.IS_WIN:
    from ctypes import wintypes

MODS = {"alt": 0x1, "ctrl": 0x2, "shift": 0x4, "win": 0x8}
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312


def _vk(key: str):
    if len(key) == 1 and key.isalnum():
        return ord(key.upper())
    if key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 12:
        return 0x70 + int(key[1:]) - 1
    if key == "space":
        return 0x20
    return None


def parse(spec: str):
    """'ctrl+shift+v' -> (modifiers, virtual-key) or (0, None) if invalid."""
    mods, vk = 0, None
    for part in [p.strip() for p in spec.lower().split("+") if p.strip()]:
        if part in MODS:
            mods |= MODS[part]
        else:
            vk = _vk(part)
    return (mods, vk) if mods and vk else (0, None)


def pretty(spec: str):
    names = {"ctrl": "Ctrl", "shift": "Shift", "alt": "Alt", "win": "Win"}
    return [names.get(p, p.upper()) for p in spec.lower().split("+") if p]


def sequence_to_string(seq):
    """QKeySequence -> 'ctrl+shift+v' (needs >= 1 modifier and a supported key)."""
    if seq.count() == 0:
        return None
    combo = seq[0]
    mods, key = combo.keyboardModifiers(), int(combo.key())
    parts = []
    if mods & Qt.KeyboardModifier.ControlModifier:
        parts.append("ctrl")
    if mods & Qt.KeyboardModifier.AltModifier:
        parts.append("alt")
    if mods & Qt.KeyboardModifier.ShiftModifier:
        parts.append("shift")
    if mods & Qt.KeyboardModifier.MetaModifier:
        parts.append("win")
    if 0x30 <= key <= 0x39 or 0x41 <= key <= 0x5A:
        name = chr(key).lower()
    elif 0x01000030 <= key <= 0x0100003B:
        name = f"f{key - 0x01000030 + 1}"
    elif key == 0x20:
        name = "space"
    else:
        return None
    if not parts:
        return None
    return "+".join(parts + [name])


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if winutil.IS_WIN and bytes(event_type) == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self.callback(int(msg.wParam))
                return True, 0
        return False, 0


def register(hotkey_id: int, spec: str) -> bool:
    mods, vk = parse(spec)
    if not winutil.IS_WIN or not vk:
        return False
    return bool(winutil.user32.RegisterHotKey(None, hotkey_id, mods | MOD_NOREPEAT, vk))


def unregister(hotkey_id: int) -> None:
    if winutil.IS_WIN:
        winutil.user32.UnregisterHotKey(None, hotkey_id)
