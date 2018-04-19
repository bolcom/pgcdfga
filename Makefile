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

# Read docker info from the actual Dockerfile
IMAGE := $(shell awk '/IMAGE:/ {print $$3}' Dockerfile)
VERSION := $(shell awk '/VERSION:/ {print $$3}' Dockerfile)
SBXPROJECT := $(shell awk '/SBXPROJECT:/ {print $$3}' Dockerfile)
STGPROJECT := $(shell awk '/STGPROJECT:/ {print $$3}' Dockerfile)

all: clean build tag push

clean:
	rm -rf pgcdfga.egg-info/
	docker rmi ${SBXPROJECT}/${IMAGE}:${VERSION} || echo Could not clean ${SBXPROJECT}/${IMAGE}:${VERSION}
	docker rmi eu.gcr.io/${SBXPROJECT}/${IMAGE}:${VERSION} || echo Could not clean eu.gcr.io/${SBXPROJECT}/${IMAGE}:${VERSION}
	docker rmi eu.gcr.io/${STGPROJECT}/${IMAGE}:${VERSION} || echo Could not clean eu.gcr.io/${STGPROJECT}/${IMAGE}:${VERSION}
	docker rmi eu.gcr.io/${SBXPROJECT}/${IMAGE}:latest || echo Could not clean eu.gcr.io/${SBXPROJECT}/${IMAGE}:latest
	docker rmi eu.gcr.io/${STGPROJECT}/${IMAGE}:latest || echo Could not clean eu.gcr.io/${STGPROJECT}/${IMAGE}:latest

run:
	docker run --rm -t ${SBXPROJECT}/${IMAGE}:${VERSION}

build: Dockerfile
	docker build -t ${SBXPROJECT}/${IMAGE}:${VERSION} -f Dockerfile .

tag: tag-version tag-latest

tag-version:
	docker tag ${SBXPROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${SBXPROJECT}/${IMAGE}:${VERSION}
	docker tag ${SBXPROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${STGPROJECT}/${IMAGE}:${VERSION}

tag-latest:
	docker tag ${SBXPROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${SBXPROJECT}/${IMAGE}:latest
	docker tag ${SBXPROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${STGPROJECT}/${IMAGE}:latest

push: push-version push-latest

push-version:
	gcloud docker -- push eu.gcr.io/${STGPROJECT}/${IMAGE}:${VERSION} || echo Could not push eu.gcr.io/${STGPROJECT}/${IMAGE}:${VERSION}
	gcloud docker -- push eu.gcr.io/${SBXPROJECT}/${IMAGE}:${VERSION} || echo Could not push eu.gcr.io/${SBXPROJECT}/${IMAGE}:${VERSION}

push-latest:
	gcloud docker -- push eu.gcr.io/${STGPROJECT}/${IMAGE}:latest || echo Could not push eu.gcr.io/${STGPROJECT}/${IMAGE}:latest
	gcloud docker -- push eu.gcr.io/${SBXPROJECT}/${IMAGE}:latest || echo Could not push eu.gcr.io/${SBXPROJECT}/${IMAGE}:latest

test:
	flake8 .
	coverage run --source pgcdfga setup.py test
	coverage report -m
