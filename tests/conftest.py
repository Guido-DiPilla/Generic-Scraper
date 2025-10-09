"""Adjust sys.path so tests can import the Modern_Refactored package when running pytest from this folder.
This avoids needing an installed package or a different working directory.
"""
import sys
from pathlib import Path

# Add the directory above the package folder to sys.path
# tests/ -> Modern_Refactored/ -> parent
ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))
