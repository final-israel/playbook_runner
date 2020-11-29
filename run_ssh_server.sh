#!/bin/bash

# apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
# python3 -m ensurepip
# pip3 install --no-cache --upgrade pip setuptools

docker run -d \                                                                                                                                                                                        ~
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
  --restart unless-stopped \
  ghcr.io/linuxserver/openssh-server
