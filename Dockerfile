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

# IMAGE:          crunchy-pgcdfga
# VERSION:        0.9.4
# STGPROJECT:     bolcom-stg-baseimages-702
# SBXPROJECT:     bolcom-sbx-baseimages-fd0 
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

COPY pgcdfga /usr/src/app/pgcdfga/
COPY setup.cfg setup.py /usr/src/app/

RUN pip install --no-cache-dir .

#RUN groupadd -r -g 999 pgcdfga && useradd -m --no-log-init -r -g pgcdfga -u 999 pgcdfga && mkdir ~pgcdfga/conf ~pgcdfga/.postgresql ~pgcdfga/.ldap_secrets && chown pgcdfga: ~pgcdfga/conf ~pgcdfga/.postgresql ~pgcdfga/.ldap_secrets && chmod 600 ~pgcdfga/conf ~pgcdfga/.postgresql ~pgcdfga/.ldap_secrets

#USER 999

ENTRYPOINT ["pgcdfga"]
