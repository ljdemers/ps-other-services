#!/bin/bash
echo "##### Running Pylint checks..."
pylint --rcfile=.pylintrc \
    ports ships \
    > reports/pylint.txt
