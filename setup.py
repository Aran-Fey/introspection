
import importlib.machinery
import importlib.util
import setuptools
import sys
from pathlib import Path


HERE = Path(__file__).parent


def import_package_from_path(path):
    name = path.stem
    origin = str(path / '__init__.py')

    loader = importlib.machinery.SourceFileLoader(name, origin)
    spec = importlib.util.spec_from_file_location(name, origin, loader=loader)
    module = importlib.util.module_from_spec(spec)

    # add the module to sys.path before executing it so that relative imports work
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


author = "Aran-Fey"

name = HERE.name
long_description = (HERE / "README.md").read_text()

module = importlib.import_module(name)

setuptools.setup(
    name=name,
    version=module.__version__,
    author=author,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/{}/{}".format(author, name),
    packages=[name],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
