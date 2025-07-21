"""
HealthLang AI MVP - Bilingual Medical Q&A System

A FastAPI-based application providing Yoruba-English medical question answering
with Groq-accelerated LLMs and RAG integration.
"""

__version__ = "0.1.0"
__author__ = "HealthLang AI Team"
__email__ = "team@healthlang.ai"

from .main import app

__all__ = ["app"] 