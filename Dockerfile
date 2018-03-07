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

# IMAGE:          bolcom-pgcdfga
# VERSION:        0.8
# PROJECT:        bolcom-stg-baseimages-702
# AUTHOR:         BOL-DBA <bol-dba@bol.com>
# DESCRIPTION:    Enforces Postgres CrunchyData Fine Grained Authorization
# TO_BUILD/TAG:   make
# TO_PUSH:        make push

FROM python:3.6.4

LABEL maintainer=bol-dba@bol.com

LABEL com.bol.docker.description="Utility container to sync postgres roles, users, databases and extensions from yaml and ldap"
LABEL com.bol.docker.usage="Start scheduled without arguments. Add config with configmaps."
LABEL com.bol.docker.type="utility"
LABEL com.bol.docker.documentation="README"
LABEL com.bol.docker.opex="bol-dba"


WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --no-cache-dir .

ENTRYPOINT ["pgcdfga"]
