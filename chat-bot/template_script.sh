#!/bin/bash

# Proxy
# export http_proxy=
# export https_proxy=
# export no_proxy=

# Mattermost
export MATTERMOST_URL=http://127.0.0.1
export MATTERMOST_PORT=8065
export MATTERMOST_API_PATH=/api/v4
export BOT_TOKEN=

# Gemini API
export GEMINI_MODEL=gemini-pro
export GEMINI_API_KEY=

python3 gemini-chat-bot.py
