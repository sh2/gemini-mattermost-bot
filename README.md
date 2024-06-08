# gemini-mattermost-bot

This is a Mattermost Bot that uses Gemini API as its backend.

## Setup

First, create a Bot account with Mattermost's integration feature.
The bot's name should begin with "ai-".

The following is the setup procedure for launching Python scripts directly.

```bash
git clone https://github.com/sh2/gemini-mattermost-bot.git
cd gemini-mattermost-bot/chat-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp template_script.sh script.sh
vim script.sh
./script.sh
```

The following is the setup instructions for building a Podman/Docker container.

```bash
git clone https://github.com/sh2/gemini-mattermost-bot.git
cd gemini-mattermost-bot/chat-bot
podman build -t gemini-chat-bot .
cp template_container.sh container.sh
vim container.sh
./container.sh
```

## Config

Set the following environment variables.
Please refer to `template_script.sh` and `template_container.sh`.

| Name | Required | Example |
| ---- | ---- | ---- |
| MATTERMOST_URL | yes | <http://mattermost.example.com> |
| MATTERMOST_PORT | yes | 8065 |
| MATTERMOST_API_PATH | yes | /api/v4 |
| BOT_TOKEN | yes | xxxxxxxx |
| GEMINI_MODEL | yes | gemini-1.5-flash |
| GEMINI_API_KEY | yes | yyyyyyyy |

## Usage

The bot uses the channel header as a system prompt.
Please edit the header first.

Mention the bot and it will respond with a thread.
If you reply to the thread, you can continue the conversation.
You do not need to re-mention the bot at this time.

![Chat Sample](sample_chat.png)

## License

MIT License  
Copyright (c) 2023-2024 Sadao Hiratsuka
