#!/bin/bash

docker run --rm -d \
  --name=openssh-server \
  --hostname=openssh-server `#optional` \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/London \
  -e SUDO_ACCESS=true `#optional` \
  -e PASSWORD_ACCESS=true `#optional` \
  -e USER_PASSWORD=sshpassword `#optional` \
  -e USER_NAME=sshuser `#optional` \
  -p 2222:2222 \
  -v /tmp/config:/config \
  ghcr.io/linuxserver/openssh-server

docker exec openssh-server apk add --update --no-cache python3
docker exec openssh-server ln -sf python3 /usr/bin/python
docker exec openssh-server python3 -m ensurepip
docker exec openssh-server pip3 install --no-cache --upgrade pip setuptools

