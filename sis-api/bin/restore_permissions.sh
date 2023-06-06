#!/usr/bin/env sh

# Restores permissions of all the cas/ tree files. This will make every file
# created as a result of a Docker process, like for example the static code
# analysis reports, to finally belong to the user who executed the process,
# instead of letting Docker leave all sort of artifacts owned by `root`.
echo "Setting application environment ownership before leaving..."
chown -R $HOSTUSER:$HOSTGROUP .