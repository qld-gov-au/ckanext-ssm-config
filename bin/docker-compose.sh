#!/bin/sh

set -x

# Pass commands to Docker Compose v1 or v2 depending on what is present

(env && which docker) || exit 1
if (docker compose ls >/dev/null); then
    # Docker Compose v2
    docker compose $*
elif (which docker-compose >/dev/null); then
    # Docker Compose v1
    docker-compose $*
else
    # Docker Compose not found
    exit 1
fi
