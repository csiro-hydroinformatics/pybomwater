import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
      name='pybomwater',
      version='0.0.1',
      author='Andrew Freebairn',
      author_email='andrew.freebairn@csiro.au',
      description='A tool for requesting data from BoM Water Data service.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/csiro-hydroinformatics/pybomwater",
      packages=setuptools.find_packages(),
      # packages=['bom_water',
      #           'test',
      # ],
      install_requires=[
            'requests',
            'iso8601',
            'pytz',
            'xmltodict',
            'pandas'
      ],
      zip_safe=False)


# https://packaging.python.org/tutorials/packaging-projects/
#python3 setup.py sdist bdist_wheel