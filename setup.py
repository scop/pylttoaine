#!/usr/bin/env python3

"""Pylttoaine setup."""

from setuptools import setup  # type: ignore[import]


def get_version() -> str:
    """Extract version number."""
    filename = "src/pylttoaine/__init__.py"
    with open(filename, encoding="utf-8") as file_:
        for line in file_:
            if line.startswith("__version__"):
                return line.split("=")[-1].strip("\"'\r\n ")
    raise Exception(f"No __version__ in {filename}!")


if __name__ == "__main__":
    setup(version=get_version())
