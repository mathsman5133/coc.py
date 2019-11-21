from setuptools import setup
import os

REQUIREMENTS = []
with open(os.path.join(os.getcwd(), "requirements.txt")) as f:
    REQUIREMENTS = f.read().splitlines()

VERSION = "0.3.0"

README = ""
with open("README.rst") as f:
    README = f.read()

setup(
    name="coc.py",
    author="mathsman5133",
    url="https://github.com/mathsman5133/coc.py",
    packages=["coc"],
    version=VERSION,
    license="MIT",
    description="A python wrapper for the Clash of Clans API",
    long_description=README,
    long_description_content_type="text/x-rst",
    python_requires=">=3.5.3",
    install_requires=REQUIREMENTS,
    extra_requires={"docs": ["sphinx==1.7.4", "sphinx_rtd_theme"], "lint": ["pylint"]},
)
