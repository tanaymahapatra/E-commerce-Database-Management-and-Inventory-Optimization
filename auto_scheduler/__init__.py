"""
__init__.py
===========
Makes auto_scheduler a proper Python package.
Exposes the top-level entry point for convenience.
"""

from .pipeline import run_weekly_pipeline

__all__ = ["run_weekly_pipeline"]
