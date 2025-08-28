#!/usr/bin/env python3
import sys
sys.path.insert(0, './src')
from setuptools import setup, find_packages

setup(
    name="it_internship_finder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.9.1",
        "python-telegram-bot>=20.7",
        "python-dotenv>=1.0.0",
        "firebase-admin>=6.2.0",
        "beautifulsoup4>=4.12.2",
        "feedparser>=6.0.10",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'internship-finder=main:main',
        ],
    },
)
