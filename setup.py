
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

from setuptools import setup, find_packages

install_requirements = [
    'pyyaml==3.12',
    'psycopg2-binary',
    'ldap3'
]

setup(
    name='pgcdfga',
    version='0.1',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=install_requirements,
    entry_points={
        'console_scripts': [
            'pgcdfga=pgcdfga.pgcdfga:main',
        ]
    }
)
