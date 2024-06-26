import setuptools
import re
# To use a consistent encoding
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))

verstr = 'unknown'
VERSIONFILE = "pybomwater/_version.py"
with open(VERSIONFILE, "r")as f:
    verstrline = f.read().strip()
    pattern = re.compile(r"__version__ = ['\"](.*)['\"]")
    mo = pattern.search(verstrline)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

with open("README.md", "r") as fh:
    long_description = fh.read()

CLASSIFIERS = ['Development Status :: 3 - Alpha',
                'Intended Audience :: Science/Research',
                'Topic :: Scientific/Engineering :: Hydrology',
                'License :: OSI Approved :: BSD License',
                'Operating System :: OS Independent',
                'Programming Language :: Python'
                ]

setuptools.setup(
    name='pybomwater', # package names need not start with 'py'
    version=verstr,
    description='A tool for requesting data from BoM Water Data service.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Andrew Freebairn',
    author_email='andrew.freebairn@csiro.au',
    #   packages = setuptools.find_packages(),
    packages=['pybomwater'],
    install_requires=[
        'requests',
        'iso8601',
        'wheel',
        'pytz',
        'json5',
        'xmltodict',
        'pandas',
        'geojson',
        'shapely',
    ],
    classifiers=CLASSIFIERS,
    url='https://github.com/csiro-hydroinformatics/pybomwater',
    zip_safe=False)

# https://packaging.python.org/tutorials/packaging-projects/
#python setup.py sdist bdist_wheel
#while venv is active `poetry publish`
#twine upload --repository testpypi dist/*
# or for actual pypi use the following
#twine upload --repository pypi dist/*
