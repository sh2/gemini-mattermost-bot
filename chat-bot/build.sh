#!/bin/bash

YYYYMMDD=$(date +%Y%m%d)

podman build --tag=gemini-chat-bot:${YYYYMMDD} .
