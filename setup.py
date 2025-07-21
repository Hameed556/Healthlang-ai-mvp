#!/usr/bin/env python3
"""
Setup script for HealthLang AI MVP
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version from environment or default
def get_version():
    return os.getenv("VERSION", "0.1.0")

setup(
    name="healthlang-ai-mvp",
    version=get_version(),
    author="HealthLang AI Team",
    author_email="team@healthlang.ai",
    description="Bilingual (Yoruba-English) medical Q&A system with Groq-accelerated LLMs and RAG",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/healthlang/healthlang-ai-mvp",
    project_urls={
        "Bug Tracker": "https://github.com/healthlang/healthlang-ai-mvp/issues",
        "Documentation": "https://healthlang.ai/docs",
        "Source Code": "https://github.com/healthlang/healthlang-ai-mvp",
    },
    packages=find_packages(include=["app", "app.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "gpu": [
            "torch>=2.1.2+cu118",
            "faiss-gpu>=1.7.4",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
            "mkdocstrings[python]>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "healthlang=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": [
            "data/**/*",
            "config/*.yaml",
            "config/*.json",
        ],
    },
    zip_safe=False,
    keywords=[
        "medical",
        "ai",
        "yoruba",
        "translation",
        "llm",
        "rag",
        "healthcare",
        "groq",
        "fastapi",
    ],
) 