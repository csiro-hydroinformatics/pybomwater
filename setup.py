import setuptools

setuptools.setup(name='bom_water',
      version='0.1.1',
      description='A tool for requesting data from BoM Water Data service.',
      author='C.S.I.R.O.',
    #   packages = setuptools.find_packages(),
      packages=['bom_water',
                'test',
      ],
      install_requires=[
            'requests',
            'iso8601',
            'pytz',
            'json5',
            'xmltodict',
            'os',
            'pandas'
          
      ],
      url='https://github.com/csiro-hydroinformatics/bom_water',
      zip_safe=False)


# https://packaging.python.org/tutorials/packaging-projects/
#python3 setup.py sdist bdist_wheel