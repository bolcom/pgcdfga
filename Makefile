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
PROJECT := $(shell awk '/PROJECT:/ {print $$3}' Dockerfile)

all: build tag

clean:
	rm -r pgcdfga.egg-info/

run:
	docker run --rm -t ${PROJECT}/${IMAGE}:${VERSION}

build: Dockerfile
	docker build -t ${PROJECT}/${IMAGE}:${VERSION} -f Dockerfile .

tag: tag-version tag-latest

tag-version:
	docker tag ${PROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${PROJECT}/${IMAGE}:${VERSION}

tag-latest:
	docker tag ${PROJECT}/${IMAGE}:${VERSION} eu.gcr.io/${PROJECT}/${IMAGE}:latest

push: push-version push-latest

push-version:
	gcloud docker -- push eu.gcr.io/${PROJECT}/${IMAGE}:${VERSION}

push-latest:
	gcloud docker -- push eu.gcr.io/${PROJECT}/${IMAGE}:latest

test:
	flake8 .
	coverage run --source pgcdfga setup.py test
	coverage report -m
