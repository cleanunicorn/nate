from setuptools import setup, find_packages

setup(
    name="nate",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "python-dotenv",
        # Add other dependencies as needed
    ],
    entry_points={
        "console_scripts": [
            "nate=main:cli",
        ],
    },
)
