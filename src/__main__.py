"""
Entry point for running the package as a module.

Usage:
    python -m src analyze -n 100
    python -m src single 52991
    python -m src compare 52991,5114,1735
    python -m src version
"""

from src.cli import main

if __name__ == "__main__":
    main()
