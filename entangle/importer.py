# pylint: disable=locally-disabled, multiple-statements, too-few-public-methods, unused-argument, missing-function-docstring
"""
importer.py - Automatically import missing modules from pypi
"""
from importlib import util
import subprocess
import sys


class PipFinder:
    """
    Automatically import missing modules from pypi
    """
    @classmethod
    def find_spec(cls, name, path, target=None):
        print(f"Module {name!r} not installed.  Attempting to pip install")
        cmd = f"{sys.executable} -m pip install {name}"
        try:
            subprocess.run(cmd.split(), check=True)
        except subprocess.CalledProcessError:
            return None

        return util.find_spec(name)


sys.meta_path.append(PipFinder)
