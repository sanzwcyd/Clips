from PySide6.QtCore import QObject, Signal

from . import winutil

STRINGS = {
    "en": {
        "search_ph": "Search clipboard history…",
        "tab_all": "All", "tab_text": "Text", "tab_images": "Images", "tab_pinned": "Pinned",
        "sec_pinned": "Pinned", "sec_recent": "Recent",
        "kind_text": "Text", "kind_email": "Email", "kind_image": "Image",
        "pinned_word": "pinned", "image_dim": "Image {w} × {h}",
        "now": "just now", "min_ago": "{n} min ago", "hr_ago": "{n} hr ago", "day_ago": "{n} d ago",
        "hint_select": "Select", "hint_paste": "Paste", "hint_delete": "Delete", "hint_close": "Close",
        "empty_title": "Nothing here yet",
        "empty_body": "Copy some text or an image and it will show up here.",
        "noresult_title": "No results", "noresult_body": "Try a different search.",
        "lang_auto": "Auto (follow Windows)", "lang_en": "English", "lang_id": "Bahasa Indonesia",
        "settings": "Settings", "about": "About", "close": "Close",
        "sec_general": "General", "sec_history": "History", "sec_shortcut": "Shortcut & privacy",
        "set_language": "Language", "set_startup": "Run at Windows startup",
        "set_accent": "Accent color: follow Windows", "set_keep": "Keep up to",
        "items_n": "{n} items", "set_images": "Save images", "set_clear_exit": "Clear history on exit",
        "set_hotkey": "Open history", "change": "Change",
        "set_detect": "Detect emails & passwords", "set_show_btn": "Show detection button",
        "btn_always": "Always", "btn_pw": "Only passwords", "btn_never": "Never",
        "set_btn_pos": "Button position", "pos_br": "Bottom right", "pos_bl": "Bottom left",
        "set_ignored": "Ignored apps", "manage": "Manage…", "version": "Current version: {v}",
        "tray_open": "Open history", "tray_pause": "Pause recording", "tray_clear": "Clear history",
        "tray_startup": "Run at Windows startup", "tray_settings": "Settings",
        "tray_about": "About", "tray_quit": "Quit", "quit_app": "Quit Clips",
        "about_hi": "Hi! Thanks for stopping by", "made_by": "Made by", "link_unset": "Link not set yet",
        "det_title": "Detected items", "det_emails": "Emails", "det_passwords": "Passwords",
        "det_clears": "Clears in {t}", "det_none": "Nothing detected yet",
        "det_note": "Passwords are encrypted and cleared automatically.",
        "det_copied": "Copied {t}", "det_copy": "Copy", "det_show": "Show password",
        "toast_email": "Email detected", "toast_pw": "Password detected",
        "toast_sub": "Just copied", "toast_view": "View",
        "hk_title": "Change shortcut", "hk_hint": "Press the new shortcut. Use at least one modifier (Ctrl, Alt, Shift, Win).",
        "hk_invalid": "That shortcut isn't supported. Try something like Ctrl+Shift+V.",
        "hk_taken": "Couldn't register {k}. Another app may be using it.",
        "ign_title": "Ignored apps",
        "ign_hint": "Clips won't record anything copied from these apps (for example keepass.exe).",
        "ign_ph": "app.exe", "ign_add": "Add", "ign_remove": "Remove selected",
        "save": "Save", "cancel": "Cancel", "yes": "Yes", "no": "No",
        "first_title": "Start with Windows?", "first_body": "Run Clips automatically when Windows starts?",
        "running_msg": "Clips is running. Press {k} to open your history.",
    },
    "id": {
        "search_ph": "Cari riwayat clipboard…",
        "tab_all": "Semua", "tab_text": "Teks", "tab_images": "Gambar", "tab_pinned": "Disematkan",
        "sec_pinned": "Disematkan", "sec_recent": "Terbaru",
        "kind_text": "Teks", "kind_email": "Email", "kind_image": "Gambar",
        "pinned_word": "disematkan", "image_dim": "Gambar {w} × {h}",
        "now": "baru saja", "min_ago": "{n} menit lalu", "hr_ago": "{n} jam lalu", "day_ago": "{n} hari lalu",
        "hint_select": "Pilih", "hint_paste": "Tempel", "hint_delete": "Hapus", "hint_close": "Tutup",
        "empty_title": "Belum ada isi",
        "empty_body": "Salin teks atau gambar, nanti langsung muncul di sini.",
        "noresult_title": "Tidak ada hasil", "noresult_body": "Coba kata kunci lain.",
        "lang_auto": "Otomatis (ikuti Windows)", "lang_en": "English", "lang_id": "Bahasa Indonesia",
        "settings": "Pengaturan", "about": "Tentang", "close": "Tutup",
        "sec_general": "Umum", "sec_history": "Riwayat", "sec_shortcut": "Pintasan & privasi",
        "set_language": "Bahasa", "set_startup": "Jalankan saat Windows menyala",
        "set_accent": "Warna aksen: ikuti Windows", "set_keep": "Simpan maksimal",
        "items_n": "{n} item", "set_images": "Simpan gambar", "set_clear_exit": "Hapus riwayat saat keluar",
        "set_hotkey": "Buka riwayat", "change": "Ubah",
        "set_detect": "Deteksi email & password", "set_show_btn": "Tampilkan tombol deteksi",
        "btn_always": "Selalu", "btn_pw": "Hanya password", "btn_never": "Tidak pernah",
        "set_btn_pos": "Posisi tombol", "pos_br": "Kanan bawah", "pos_bl": "Kiri bawah",
        "set_ignored": "Aplikasi yang diabaikan", "manage": "Kelola…", "version": "Versi saat ini: {v}",
        "tray_open": "Buka riwayat", "tray_pause": "Jeda perekaman", "tray_clear": "Hapus riwayat",
        "tray_startup": "Jalankan saat Windows menyala", "tray_settings": "Pengaturan",
        "tray_about": "Tentang", "tray_quit": "Keluar", "quit_app": "Keluar dari Clips",
        "about_hi": "Halo! Makasih sudah mampir", "made_by": "Dibuat oleh", "link_unset": "Link belum diatur",
        "det_title": "Item terdeteksi", "det_emails": "Email", "det_passwords": "Password",
        "det_clears": "Terhapus dalam {t}", "det_none": "Belum ada yang terdeteksi",
        "det_note": "Password dienkripsi dan dihapus otomatis.",
        "det_copied": "Disalin {t}", "det_copy": "Salin", "det_show": "Tampilkan password",
        "toast_email": "Email terdeteksi", "toast_pw": "Password terdeteksi",
        "toast_sub": "Baru saja disalin", "toast_view": "Lihat",
        "hk_title": "Ubah pintasan", "hk_hint": "Tekan pintasan baru. Gunakan minimal satu tombol modifier (Ctrl, Alt, Shift, Win).",
        "hk_invalid": "Pintasan itu tidak didukung. Coba seperti Ctrl+Shift+V.",
        "hk_taken": "Tidak bisa mendaftarkan {k}. Mungkin dipakai aplikasi lain.",
        "ign_title": "Aplikasi yang diabaikan",
        "ign_hint": "Clips tidak akan merekam apa pun yang disalin dari aplikasi ini (contoh: keepass.exe).",
        "ign_ph": "app.exe", "ign_add": "Tambah", "ign_remove": "Hapus yang dipilih",
        "save": "Simpan", "cancel": "Batal", "yes": "Ya", "no": "Tidak",
        "first_title": "Jalankan bersama Windows?", "first_body": "Jalankan Clips otomatis saat Windows menyala?",
        "running_msg": "Clips sedang berjalan. Tekan {k} untuk membuka riwayat.",
    },
}


class I18n(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.pref, self.lang = "auto", "en"

    def set_pref(self, pref: str):
        """pref: 'auto' follows the Windows display language (Indonesian -> id, else en)."""
        self.pref = pref
        new = winutil.ui_language_code() if pref == "auto" else pref
        self.lang = new if new in STRINGS else "en"
        self.changed.emit()

    def tr(self, key: str, **kw) -> str:
        s = STRINGS[self.lang].get(key) or STRINGS["en"].get(key, key)
        return s.format(**kw) if kw else s


i18n = I18n()
tr = i18n.tr
