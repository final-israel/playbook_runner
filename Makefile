NAME=playbook_runner_py3

.PHONY: build _build check-local dist check docs major _major minor _minor patch _patch _debug _publish check-local

build: check  _debug _build

_build:
	@echo "Building"

_publish:
	@echo "Publishing"
	cp ${PWD}/../versions/applications/playbook_runner/version.py ${PWD}/playbook_runner
	twine upload ${PWD}/dist/*
	git checkout -- ${PWD}/../versions/applications/playbook_runner/version.py

major: check _major _build _publish

_major:
	@echo "Major Release"
	$(eval VERSION := $(shell ver_stamp \
	--repos_path ${PWD}/../ \
	--app_version_file ${PWD}//../versions/applications/playbook_runner/version.py \
	--release_mode major --app_name ${NAME}))

minor: check _minor _build _publish

_minor:
	@echo "Minor Release"
	$(eval VERSION := $(shell ver_stamp \
	--repos_path ${PWD}/../ \
	--app_version_file ${PWD}/../versions/applications/playbook_runner/version.py \
	--release_mode minor --app_name ${NAME}))

patch: check _patch _build _publish

_patch:
	@echo "Patch Release"
	$(eval VERSION := $(shell ver_stamp \
	--repos_path ${PWD}/../ \
	--app_version_file ${PWD}/../versions/applications/playbook_runner/version.py \
	--release_mode patch --app_name ${NAME}))

_debug:
	@echo "Debug Release"
	$(eval VERSION := $(shell ver_stamp \
	--repos_path ${PWD}/../ \
	--app_version_file ${PWD}/../versions/applications/playbook_runner/version.py \
	--release_mode debug --app_name ${NAME}))

check: check-local

check-local:
	@echo "-------------------------------------------------------------"
	@echo "-------------------------------------------------------------"
	@echo "-~      Running static checks                              --"
	@echo "-------------------------------------------------------------"
	PYTHONPATH=${PWD} flake8 --version
	PYTHONPATH=${PWD} flake8 --exclude version.py \
	--ignore E402,E722,E123,E126,E125,E127,E128,E129 ${PWD}/playbook_runner/
	@echo "-------------------------------------------------------------"
	@echo "-~      Running unit tests                                 --"
	@echo "-------------------------------------------------------------"
	@echo "-------------------------------------------------------------"
	@echo "-------------------------------------------------------------"

clean:
	echo 'Nothing to clean'
