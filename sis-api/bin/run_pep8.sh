#!/bin/bash
echo "##### Running PEP8 checks..."
pep8 --config=.pep8rc . > reports/pep8.txt