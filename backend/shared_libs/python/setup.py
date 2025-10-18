"""
Shared Libraries Package Setup
Install this package in all bot environments for shared code access
"""

import os

from setuptools import find_packages, setup

# Handle missing README gracefully
readme_content = ""
if os.path.exists("README.md"):
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            readme_content = fh.read()
    except Exception:
        readme_content = "Crypto Trading Shared Libraries"
else:
    readme_content = "Shared libraries for crypto trading bot system"

setup(
    name="crypto-trading-shared",
    version="1.0.0",
    author="Crypto Trading System",
    author_email="dev@cryptotrading.com",
    description="Shared libraries for crypto trading bot system",
    long_description=readme_content,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/crypto-signal-system",
    packages=find_packages(),
    package_dir={'': '.'},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies
        "pydantic>=2.0",
        "python-dotenv>=1.0.0",
        # Database
        "sqlalchemy>=2.0.0",
        "pymysql>=1.1.0",
        "psycopg2-binary>=2.9.0",
        "redis>=5.0.0",
        "pymongo>=4.5.0",
        # Messaging
        "pika>=1.3.0",
        # Utilities
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "ta>=0.11.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add CLI commands if needed
        ],
    },
    zip_safe=False,
)