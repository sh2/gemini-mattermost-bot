#!/bin/bash

podman run \
        --detach \
        --restart=always \
        --env=http_proxy= \
        --env=https_proxy= \
        --env=no_proxy= \
        --env=MATTERMOST_URL=http://127.0.0.1 \
        --env=MATTERMOST_PORT=8065 \
        --env=MATTERMOST_API_PATH=/api/v4 \
        --env=BOT_TOKEN= \
        --env=GEMINI_MODEL=gemini-1.5-flash \
        --env=GEMINI_API_KEY= \
        --name=gemini-chat-bot \
        gemini-chat-bot:20240101
