from setuptools import setup, find_packages

setup(
    name="sso-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click"
    ],
    entry_points={
        "console_scripts": [
            "sso-cli=sso_cli.cli:cli"
        ]
    },
)
