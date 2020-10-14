import subprocess
from pathlib import Path

from setuptools import setup, Command

REQUIREMENTS = Path("./requirements.txt").read_text().splitlines()

VERSION = "1.0.1"

if "a" in VERSION:
    VERSION += "+" + subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()

README = Path("README.rst").read_text()


class LintCommand(Command):
    description = "Lint's the project code."
    user_options = [("subcommands=", None, "input directory")]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pylint = """python -m pylint coc
                        --disable=too-many-instance-attributes,too-many-public-methods,too-many-lines,too-few-public-methods,duplicate-code,bad-continuation,raise-missing-from
                        --max-line-length=120
                        --notes=fixme
                        --output-format=colorized
                        --ignore=examples,docs
                        --ignored-modules=aiohttp
                 """
        self.spawn(pylint.split())
        self.spawn("python -m black --check --verbose --diff --line-length=120 --exclude=.pyi coc docs".split())
        self.spawn("python -m flake8 coc --max-line-length=120 --exclude=coc/__init__.py".split())
        self.spawn("sphinx-build -W docs/ /tmp/foo --keep-going -T".split())


setup(
    name="coc.py",
    author="mathsman5133",
    url="https://github.com/mathsman5133/coc.py",

    package_data={"coc": ["events.pyi"]},
    packages=["coc", "coc.ext.discordlinks"],
    version=VERSION,
    license="MIT",
    description="A python wrapper for the Clash of Clans API",
    long_description=README,

    python_requires=">=3.5.3",
    install_requires=REQUIREMENTS,
    extras_require={"docs": ["sphinx", "sphinx_rtd_theme", "sphinxcontrib_trio", "autodocsumm"]},
    classifiers={
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    },

    cmdclass={"lint": LintCommand},
)
