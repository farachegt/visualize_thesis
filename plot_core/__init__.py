"""Reusable plotting core for the thesis visualization project.

This package intentionally keeps `__init__` lightweight to avoid importing
heavy optional dependencies, such as `matplotlib`, when users only need
submodules like readers or geometry handlers.
"""
