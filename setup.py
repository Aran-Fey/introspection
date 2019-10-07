
import os.path
import re
import setuptools

HERE = os.path.dirname(os.path.abspath(__file__))


def extract_version():
    path = os.path.join(HERE, name, '__init__.py')
    with open(path) as file:
        code = file.read()

    pattern = re.compile(r'''^__version__\s*=\s*["']([^"']+)''', re.M)
    match = pattern.search(code)
    return match.group(1)


author = "Aran-Fey"

packages = setuptools.find_packages()
name = packages[0]

with open(HERE+"/README.md") as file:
    long_description = file.read()

version = extract_version()

setuptools.setup(
    name=name,
    version=version,
    author=author,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/{}/{}".format(author, name),
    packages=packages,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
