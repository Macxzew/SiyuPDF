import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_PATH = os.path.join(BASE_DIR, "src")
RESULTS_PATH = os.path.join(BASE_DIR, "src")
TMP_WATERMARK_PATH = os.path.join(RESOURCES_PATH, "tmp_watermark.png")
TMP_PDF_PATH1 = os.path.join(RESOURCES_PATH, "tmp_pdf1.pdf")
TMP_PDF_PATH2 = os.path.join(RESOURCES_PATH, "tmp_pdf2.pdf")
FONT_PATH = os.path.join(RESOURCES_PATH, "arial.ttf")
