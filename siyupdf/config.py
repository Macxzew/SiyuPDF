# siyupdf/config.py
from pathlib import Path
import os
from importlib import resources

# cache/app data
if os.name == "nt":
    CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "siyupdf"
else:
    CACHE_DIR = Path.home() / ".cache" / "siyupdf"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

RESOURCES_PATH = CACHE_DIR
RESULTS_PATH = Path.cwd()

TMP_WATERMARK_PATH = str(RESOURCES_PATH / "tmp_watermark.png")
TMP_PDF_PATH1      = str(RESOURCES_PATH / "tmp_pdf1.pdf")
TMP_PDF_PATH2      = str(RESOURCES_PATH / "tmp_pdf2.pdf")

def _find_arial() -> str:
    # 0) ENV prioritaire
    env = os.environ.get("SIYUPDF_ARIAL_PATH")
    if env and Path(env).exists():
        return str(Path(env).resolve())

    # 1) Fichier packagé local (si tu as copié arial.ttf dans siyupdf/data)
    try:
        ff = resources.files("siyupdf").joinpath("data/arial.ttf")
        with ff.open("rb") as _:
            return str(ff)
    except Exception:
        pass

    # 2) Windows système
    win_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\ARIAL.TTF",
    ]
    for p in win_paths:
        if Path(p).exists():
            return p

    # 3) Linux/BSD: paquets mscorefonts (ou copie manuelle)
    linux_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",
        "/usr/share/fonts/TTF/Arial.ttf",
        "/usr/local/share/fonts/arial.ttf",
        str(Path.home() / ".local/share/fonts/arial.ttf"),
        str(Path.home() / ".fonts/arial.ttf"),
    ]
    for p in linux_paths:
        if Path(p).exists():
            return p

    # 4) macOS
    mac_paths = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in mac_paths:
        if Path(p).exists():
            return p

    # 5) introuvable
    return ""  # géré en fallback dans process.py

FONT_PATH = _find_arial()
