#!/usr/bin/env python3

import os
import glob
import shutil
from setuptools import setup
from setuptools import Command

# get key package details from py_pkg/__version__.py
about = {}  # type: ignore
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'entangle', '__version__.py')) as f:
    exec(f.read(), about)

# load the README file and use it as the long_description for PyPI
with open('README.md', 'r') as f:
    readme = f.read()


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./entangle.log ./.pytest_cache ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(
                os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError(
                        "%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                try:
                    shutil.rmtree(path)
                except:
                    os.remove(path)


# package configuration - for reference see:
# https://setuptools.readthedocs.io/en/latest/setuptools.html#id9
setup(
    name=about['__title__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    packages=['entangle', 'entangle.logging', 'entangle.examples', 'entangle.tests'],
    include_package_data=True,
    python_requires="==3.8.*",
    install_requires=[
        'scp==0.13.3',
        'astunparse==1.6.3',
        'async-timeout==3.0.1',
        'cachetools==4.2.1',
        'certifi==2020.12.5',
        'cffi==1.14.3',
        'cryptography==3.2.1',
        'dill==0.3.3',
        'docker==5.0.0',
        'filelock==3.0.12',
        'gast==0.4.0',
        'globus-sdk==2.0.1',
        'numba==0.53.1',
        'numpy==1.19.2',
        'paramiko==2.7.2',
        'pip==20.2.4',
        'pipenv==2020.11.15',
        'psutil==5.8.0',
        'py-cpuinfo==8.0.0',
        'pytest==6.2.4',
        'requests==2.24.0',
        'scipy==1.6.2',
        'setuptools',
        'six==1.15.0',
        'typeguard==2.12.0',
        'dill',
        'astunparse==1.6.3'

    ],
    license=about['__license__'],
    zip_safe=False,
    cmdclass={
        'clean': CleanCommand,
    },
    entry_points={

    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='parallel processing, devops, dataflow, supercomputing, workflows'
)
