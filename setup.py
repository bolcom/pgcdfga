
# Copyright (C) 2018 Bol.com
#
# This file is part of pgcdfga.
#
# pgcdfga is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pgcdfga is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pgcdfga.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import os
import re
from setuptools import setup, find_packages

install_requirements = [
    'pyyaml==3.12',
    'psycopg2-binary',
    'ldap3'
]

def find_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, 'pgcdfga', '__init__.py'), 'r') as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='pgcdfga',
    version=find_version(),
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=install_requirements,
    entry_points={
        'console_scripts': [
            'pgcdfga=pgcdfga.pgcdfga:main',
        ]
    }
)
