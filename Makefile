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
VERSION := $(shell cat pgcdfga/__init__.py | grep "^__version__" | awk '{print $$3}' | tr -d '"')
PROJECTS := eu.gcr.io/bolcom-stg-baseimages-702 eu.gcr.io/bolcom-sbx-baseimages-fd0

all: clean test build tag push
all-latest: clean test build tag-latest push-latest
test: test-flake8 test-pylint test-coverage

clean:
	@docker rmi $(IMAGE):$(VERSION) || echo Could not clean $(IMAGE):$(VERSION)
	@$(foreach project, $(PROJECTS), docker rmi $(project)/$(IMAGE):$(VERSION) || echo Could not clean $(project)/$(IMAGE):$(VERSION))
	@$(foreach project, $(PROJECTS), docker rmi $(project)/$(IMAGE):latest || echo Could not clean $(project)/$(IMAGE):latest)

run:
	docker run --rm -t ${IMAGE}:${VERSION}

build: Dockerfile
	docker build -t ${IMAGE}:${VERSION} -f Dockerfile .

tag: tag-version tag-latest

tag-version:
	$(foreach project, $(PROJECTS), docker tag $(IMAGE):$(VERSION) $(project)/$(IMAGE):$(VERSION))

tag-latest:
	$(foreach project, $(PROJECTS), docker tag $(IMAGE):$(VERSION) $(project)/$(IMAGE):latest)

push: push-version push-latest

push-version:
	@$(foreach project, $(PROJECTS), docker push $(project)/$(IMAGE):$(VERSION) || echo Could not push $(project)/$(IMAGE):$(VERSION))

push-latest:
	@$(foreach project, $(PROJECTS), docker push $(project)/$(IMAGE):latest || echo Could not push $(project)/$(IMAGE):latest)

test-flake8:
	flake8 .

test-pylint:
	pylint *.py pgcdfga tests

test-coverage:
	coverage run --source pgcdfga setup.py test
	coverage report -m
