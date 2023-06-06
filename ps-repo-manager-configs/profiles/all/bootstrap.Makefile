.PHONY: help
.DEFAULT: help

# This target is needed to allow for the (local) help to be shown at the bottom.
# DO NOT EDIT OR REMOVE.
help::

# Add help descriptions of your project specific commands here.
# Use format: <command> - <description>
service-help:
	@echo "= Repo repeatable commands ="
	@echo ""

-include make/*

help:: service-help

pr-tests:
	false # FIXME set to PR tests set run or set to `true` if not desired
