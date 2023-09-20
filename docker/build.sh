#!/usr/bin/bash

docker buildx build --ssh default=$SSH_AUTH_SOCK -f polytut.dockerfile -t polytut .
