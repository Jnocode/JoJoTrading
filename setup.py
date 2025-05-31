"""
JoJoTrading Setup Configuration
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="jojo-trading",
    version="1.0.0",
    author="JoJoTrading Development Team",
    description="台股智慧投資分析系統",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jojo-trading",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements("requirements/base.txt") if os.path.exists("requirements/base.txt") else [],
    extras_require={
        "dev": read_requirements("requirements/dev.txt") if os.path.exists("requirements/dev.txt") else [],
        "test": read_requirements("requirements/test.txt") if os.path.exists("requirements/test.txt") else [],
    },
    entry_points={
        "console_scripts": [
            "jojo-trading=jojo_trading.ui.app:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
