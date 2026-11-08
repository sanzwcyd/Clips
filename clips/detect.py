import re

EMAIL = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9\-]+(\.[A-Z0-9\-]+)*\.[A-Z]{2,}", re.I)


def is_email(text: str) -> bool:
    return EMAIL.fullmatch(text.strip()) is not None


def looks_like_password(text: str) -> bool:
    """Heuristic only: passwords have no fixed format, so this can be wrong."""
    t = text.strip()
    if not 8 <= len(t) <= 64 or any(c.isspace() for c in t):
        return False
    if "://" in t or t.startswith(("/", "\\", "www.")) or ":\\" in t or is_email(t):
        return False
    classes = sum([any(c.islower() for c in t), any(c.isupper() for c in t),
                   any(c.isdigit() for c in t), any(not c.isalnum() for c in t)])
    return classes >= 3


def classify(text: str, flagged_sensitive: bool) -> str:
    """'password' | 'email' | 'text'. The clipboard flag set by password managers
    is the reliable signal; the heuristic is only a fallback."""
    if flagged_sensitive or looks_like_password(text):
        return "password"
    if is_email(text):
        return "email"
    return "text"
