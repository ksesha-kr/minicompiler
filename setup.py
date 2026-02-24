from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="minicompiler",
    version="0.1.0",
    author="Команда лялялябебебе",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ksesha-kr/minicompiler",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "minicompiler-lex=lexer.scanner:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="compiler lexer scanner education",
    project_urls={
        "Source": "https://github.com/ksesha-kr/minicompiler",
        "Documentation": "https://github.com/ksesha-kr/minicompiler/docs",
    },
)