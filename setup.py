from setuptools import setup, Command
import os

REQUIREMENTS = []
with open(os.path.join(os.getcwd(), "requirements.txt")) as f:
    REQUIREMENTS = f.read().splitlines()

VERSION = "1.0.0a0"

README = ""
with open("README.rst") as f:
    README = f.read()


class LintCommand(Command):
    description = "Lint's the project code."
    user_options = [
        ("subcommands=", None, "input directory"),
    ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.spawn(["python", "-m", "pylint", "coc"])
        self.spawn(
            ["python", "-m", "black", "--check", "-v", "--diff", "-l", "120", "--exclude=.pyi", "coc", "docs"]  # noqa
        )
        self.spawn(["python", "-m", "flake8", "coc"])
        # self.spawn(["sphinx-build", "-W", "docs/", "/tmp/foo", "--keep-going", "-T"])


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
    dependency_links=["https://github.com/mathsman5133/asqlite#egg=asqlite"],
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    cmdclass={"lint": LintCommand},
)
