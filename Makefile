# Makefile for edtext.

.PHONY: help clean tools

.DEFAULT_GOAL := help

help:		## Display this help message.
	@echo "Please use \`make <target>' where <target> is one of:"
	@awk -F ':.*?## ' '/^[a-zA-Z]/ && NF==2 {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

clean:		## Remove stuff we don't need.
	find . -name '__pycache__' -exec rm -rf {} +
	rm -fr build/ dist/ src/*.egg-info

install:	## Install the development tools.
	uv pip install -e '.[dev]'

test:		## Run the test suite.
	coverage run --branch -m pytest
	coverage report -m
