#!/usr/bin/env python

from setuptools import setup
from glob import glob

packages = ['sldr']

scripts = set(filter(lambda x: x.rfind(".") == -1, glob('scripts/*')))

setup(name='sldr',
      version='0.7.5',
      description='python package and scripts for working with SLDR',
      long_description="""Modules and scripts useful for working with SLDR.""",
      maintainer='David Rowe',
      maintainer_email='david_rowe@sil.org',
      url='http://github.com/silnrsi/sldrtools',
      packages=packages,
      scripts=scripts,
      license='LGPL',
      platforms=['Linux', 'Win32', 'Mac OS X'],
      package_dir={'': 'lib'},
      package_data={'sldr': ['allkeys.txt',
                             'language-subtag-registry.txt',
                             'likelySubtags.xml',
                             'sil.dtd',
                             'supplementalData.xml',
                             'supplementalMetadata.xml']}
      )
