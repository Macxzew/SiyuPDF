# setup.py
from pathlib import Path
from setuptools import setup, find_packages

def read_requirements():
    p = Path("requirements.txt")
    if p.exists():
        return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    # Fallback compatibles Python 3.9–3.13
    return [
        "cryptography>=42",
        "reportlab>=4.1",
        "asn1crypto>=1.5.1",
        "pymupdf>=1.24.10",
        "pikepdf>=9.0.0",
        "Pillow>=11.0.0",
        "colorama>=0.4.6",
    ]

README = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""

setup(
    name="siyupdf",
    version="1.0.0",
    author="Maxzew",
    description="A tool for PDF processing with siyupdf",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={"siyupdf": ["data/arial.ttf"]},  # mets le fichier dans siyupdf/data/arial.ttf
    entry_points={"console_scripts": ["siyupdf=siyupdf.main:main"]},
    install_requires=read_requirements(),
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
