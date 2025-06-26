from setuptools import setup, find_packages

setup(
    name="siyupdf",
    version="1.0",
    author="Maxzew",
    description="A tool for PDF processing with siyupdf",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "siyupdf = siyupdf.main:main",
        ],
    },
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.6",
    package_data={
        "siyupdf": ["../src/arial.ttf"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
