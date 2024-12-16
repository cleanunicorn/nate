import os
from setuptools import setup, find_packages

setup(
    name="nate",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openai",
        "tweepy",
        "click",
        "python-dotenv",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "nate=main:cli",
        ],
    },
    author="Daniel Luca",
    author_email="lucadanielcostin@gmail.com",
    description="An AI-powered Twitter bot that generates and posts tweets",
    long_description=open("README.md", encoding="utf-8").read()
    if os.path.exists("README.md")
    else "",
    long_description_content_type="text/markdown",
    url="https://github.com/cleanunicorn/nate",
    classifiers=[],
    python_requires=">=3.10",
)
