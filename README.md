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

## Make

## Make build

Will build the docker image from Dockerfile, using variables in Dockerfile to determine image name, version and project.

```
make build
```

### Make tag

Will tag images for usage in gcloud, using variables in Dockerfile to determine image name, version and project.

Will tag both latest and version.

```
make tag
```

### Make push

Will push latest and versioned images to gcloud, using variables in Dockerfile to determine image name, version and project.

```
make push
```

### Make run

Runs the built image, using variables in Dockerfile to determine image name, version and project. Using the --rm flag to keep the system clean.

```
make run
```

### Make all

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

# Developing
Developing is done in-house of Bol.com.

## New minor release:
The very latest and greatest is always in master. So if we are working on 0.9.3, everything up until 0.9.2 is tagged. To tag 0.9.3, do the following:
* First run `make clean` (you will raise the version in Dockerfile after which `make clean` does not clean older versions)
* The freeze the current minor release by tagging it (on https://gitlab.tools.bol.com/SDCR/pgcdfga/tags click `new tag`)
 * Also add a list of all patches of this minor release to the changelog
 * use `git log` if commit messages are properly formatted
 * use `git show` for a certain commit if you are unsure of one
 * use `git diff` if you are unsure of al (e.a. git diff 0.9.2)
* Finish by commiting the version change
 * Change the version of the package, which is listed in pgcdfga/__init__.py to reflect the new release
 * Use 'Raising version to [new_version]' for the commit message
 * This will be the first commit after freezing the previous version

Note: Up until 0.9.3 this procedure is not followed thoroughly enough...

## New major releas
The very latest and greatest is always in master. So if we are currently working on major 0.9, every major up until 0.8 is a branch.
To start developing 1.0, you should create a 0.9 branch that points to the latest of 0.9 development, and after that change version info in master.
* First run `make clean` (you will raise the version in Dockerfile after which `make clean` does not clean older versions)
* Create a new branch 
 * on https://gitlab.tools.bol.com/SDCR/pgcdfga/branches click on `new branch`
 * create from master
* Finish by commiting the version change
 * Change the version of the package, which is listed in pgcdfga/__init__.py to reflect the new release
 * Use 'Raising version to [new_version]' for the commit message
 * Commit this version change as a first commit in the new branch (using merge requests)

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
