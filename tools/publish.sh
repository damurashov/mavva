#!/usr/bin/bash

cd ..  \
	&& python3 -m pip install build twine \
	&& rm -rf dist \
	&& python3 -m build \
	&& python3 -m twine upload dist/*  --verbose

