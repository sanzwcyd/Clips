import os
import sys
from pathlib import Path


def resource(rel: str) -> str:
    """Path to a bundled file (works from source and from a PyInstaller build)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return str(base / rel)


def data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    d = Path(base) / "Clips"
    d.mkdir(parents=True, exist_ok=True)
    return d
