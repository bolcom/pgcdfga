# PGCDFGA - Postgres CrunchyData Fine Grained Access tool

Tool to configure Postgres logical objects, being Users, Roles, Databases and Extensions.

The provided Makefile takes care of most docker/gcloud stuff.

## Requirements

### PGCDFGA config

R2d2 will  craete a configuration yaml that will configure this instance of the PGCDFGA container.

### Postgres User account

For running the PGCDFGA tool, the PGCDFGA tool requires a postgres user with access and SUPERUSER privilleges.
This could be brought available, either with:
- local access (when running inside of master container) and using ident (or trust) authentication
- A username / password configured with setup.sql script (and setting PG_PRIMARY_USER, PG_PRIMARY_PASSWORD, etc.).
- A client certificate (which is by far the most secure solution)

The most convenient way is to use a client certificate, handed out to PGCDFGA user as configured in config.yaml (postgres.dsn).

## Build

Will build the docker image from Dockerfile, using variables in Dockerfile to determine image name, version and project.

```
make build
```

## Tag

Will tag images for usage in gcloud, using variables in Dockerfile to determine image name, version and project.

Will tag both latest and version.

```
make tag
```

## Push

Will push latest and versioned images to gcloud, using variables in Dockerfile to determine image name, version and project.

```
make push
```

## Run

Runs the built image, using variables in Dockerfile to determine image name, version and project. Using the --rm flag to keep the system clean.

```
make run
```

## All

Will use build and tag as described above. Pushing is not included (yet)

```
make
```

## Example:
* First build the container image:
```
make
```
* Request server certificates, generate client cerificates and configure the Postgres database server accordingly
* Store serverca cert in testdata/sererca.pem
* Store client cert in testdata/client_pgcdfga_chain.pem and key in testdata/client_pgcdfga.key (in kubernetes this will be secrets mounted as a volume)
* store ldap user / password in seperate files (in kubernetes this will be secrets mounted as a volume)
* configure testdata/config.yaml correctly (e.a. hostname, location of ldap user/pw files, etc.)
* start the container
```
docker run --rm -v $PWD:/pgcdfga_config bolcom-stg-baseimages-702/pgcdfga:0.1
```

et voila

# PGCDFGA Disclaimer:

Copyright (C) 2018 Bol.com
This file is part of pgcdfga.

pgcdfga is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pgcdfga is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pgcdfga.  If not, see <http://www.gnu.org/licenses/>.
