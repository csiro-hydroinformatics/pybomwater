import setuptools
import re
# To use a consistent encoding
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))

verstr = 'unknown'
VERSIONFILE = "bom_water/_version.py"
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
                'License :: BSD-3',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Programming Language :: Python :: 3.6',
                'Programming Language :: Python :: 3.7'
                ]

setuptools.setup(
    name='bomwater', # package names need not start with 'py'
    version=verstr,
    description='A tool for requesting data from BoM Water Data service.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Andrew Freebairn',
    author_email='andrew.freebairn@csiro.au',
    #   packages = setuptools.find_packages(),
    packages=['bom_water'],
    install_requires=[
        'requests',
        'iso8601',
        'pytz',
        'json5',
        'xmltodict',
        'pandas'
    ],
    classifiers=CLASSIFIERS,
    url='https://github.com/csiro-hydroinformatics/pybomwater',
    zip_safe=False)

# https://packaging.python.org/tutorials/packaging-projects/
#python3 setup.py sdist bdist_wheel