# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('taskmage/taskmage.py').read(),
    re.M
    ).group(1)


with open("README.md", "rb") as f:
    long_description = f.read().decode("utf-8")


setup(
    name = "taskmage",
    packages = ["taskmage", "taskmage.db"],
    entry_points = {
        "console_scripts": ['taskmage = taskmage.taskmage:main']
    },
    version = version,
    description = "Time tracking for taskwarrior",
    long_description = long_description,
    author = "Christiaan B van Zyl",
    author_email = "christiaanvanzyl@gmail.com",
    url = "https://github.com/mozey/taskmage",
    install_requires = [
        "SQLAlchemy>=1.0.8",
        "argparse>=1.4.0",
    ]
)