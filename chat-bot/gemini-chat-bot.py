import google.generativeai
import httpx
import json
import logging
import os
import re
import threading
import time
import traceback
import websocket

from mmpy_bot import (
    Bot,
    Message,
    Plugin,
    Settings,
    listen_to
)

log = logging.getLogger("gemini-chat-bot")


class ChatBot(Plugin):
    def __init__(self):
        super().__init__()

        # Gemini API
        # gRPC does not support SOCKS5 proxy, so use REST
        google.generativeai.configure(
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            transport="rest"
        )

        self.gemini_model = google.generativeai.GenerativeModel(
            os.environ.get("GEMINI_MODEL", "gemini-pro")
        )

        # Mattermost
        self.is_typing = True

        self.websocket_auth = {
            "seq": 1,
            "action": "authentication_challenge",
            "data": {
                "token": ""
            }
        }

        self.websocket_typing = {
            "action": "user_typing",
            "seq": 2,
            "data": {
                "channel_id": "",
                "parent_id": ""
            }
        }

    @listen_to("")
    def respond(self, message: Message):
        if self.driver is None:
            raise ValueError("self.driver is None")

        if self.settings is None:
            raise ValueError("self.setting is None")

        self.is_typing = True
        self.websocket_auth["data"]["token"] = self.settings.BOT_TOKEN
        self.websocket_typing["data"]["channel_id"] = message.channel_id

        # Use message.root_id. Note that message.parent_id is not defined.
        self.websocket_typing["data"]["parent_id"] = message.root_id

        # Get the entire thread.
        thread = self.driver.get_post_thread(message.id)

        # If you use needs_mention in the listen_to decorator,
        # you can only see the last remark, so don't use this,
        # but look at the whole thread to determine if you should reply to the message.
        if not self.is_reply_required(thread, message.sender_name):
            return

        # Get channel headers and use them as context.
        channels = self.driver.channels  # type: ignore
        context = channels.get_channel(message.channel_id)["header"]

        # Assemble the request message.
        # TODO: Check if the number of tokens is exceeded.
        requestMessages = self.build_request_messages(
            thread, self.driver.user_id, context)
        log.info("API Request: " +
                 json.dumps(requestMessages, ensure_ascii=False))

        try:
            # Start typing.
            # Connect separately as I cannot find a way to use the WebSocket connection
            # used by the bot itself.
            ws = websocket.WebSocket()
            ws.connect(self.build_websocket_url())
            ws.send(json.dumps(self.websocket_auth))
            self.send_typing(ws)

            # Call Gemini API
            response = self.gemini_model.generate_content(
                requestMessages, stream=True)

            # Reply with an empty message and update with stream data.
            reply = self.driver.reply_to(message, "")
            reply_id = reply["id"]
            reply_chunks = []
            last_time = time.time()

            for chunk in response:
                reply_chunks.append(chunk.text)
                current_time = time.time()

                # Stores stream data for one second before outputting it.
                if last_time + 1.0 <= current_time:
                    last_time = current_time
                    reply_messages = "".join(reply_chunks)
                    reply_chunks = [reply_messages]

                    self.driver.posts.update_post(  # type: ignore
                        post_id=reply_id,
                        options={
                            "id": reply_id,
                            "message": reply_messages + "▌"
                        }
                    )

            # Update again with the last set of data.
            reply_messages = "".join(reply_chunks)
            log.info("API Response: " + reply_messages)

            self.driver.posts.update_post(  # type: ignore
                post_id=reply_id,
                options={
                    "id": reply_id,
                    "message": reply_messages
                }
            )
        except Exception:
            stacktrace = traceback.format_exc()
            log.error(f"Exception:\n{stacktrace}")
            self.driver.create_post(
                message.channel_id, f"Exception occured.\n```{stacktrace}```")
        finally:
            # Stop typing.
            self.is_typing = False

    def is_reply_required(self, thread, sender_name: str) -> bool:
        """
        Determine if the bot should reply to the thread.
        """

        if self.driver is None:
            raise ValueError("self.driver is None")

        # To prevent bots from talking to each other,
        # do not reply to messages by users beginning with "ai-".
        if sender_name.startswith("ai-"):
            return False

        # Reply to any mentions of the bot in the thread.
        # I couldn't find a function to extract mentions in mmpy_bot,
        # so I extracted them on my own.
        # username regex pattern: @([a-z0-9\.\-_]+)
        username_escaped = self.driver.username.replace(".", "\\.")
        pattern = fr"(^|\s)@{username_escaped}(?=$|\s)"

        for post_id in thread["order"]:
            if re.search(pattern, thread["posts"][post_id]["message"]):
                return True

        # If the conditions up to this point are not met, the bot will not reply.
        return False

    def build_request_messages(self, thread, bot_id, context) -> list:
        """
        Assemble and return a message list to pass to the OpenAI API
        based on the content of the thread.
        """

        if self.driver is None:
            raise ValueError("self.driver is None")

        requestMessages = []

        for post_id in thread["order"]:
            post = thread["posts"][post_id]
            if post["user_id"] == bot_id:
                requestMessages.append(
                    {"role": "model", "parts": [post["message"]]})
            else:
                # Remove mentions of the bot.
                message = post["message"].replace(
                    "@" + self.driver.username, "")

                if len(requestMessages) == 0:
                    # Add context to the first message.
                    requestMessages.append(
                        {
                            "role": "user",
                            "parts": ["Context: " + context + "\nMessage: " + message]
                        }
                    )
                else:
                    requestMessages.append(
                        {"role": "user", "parts": message})

        return requestMessages

    def build_websocket_url(self) -> str:
        """
        Assemble and return WebSocket connection URL.
        """

        if self.settings is None:
            raise ValueError("self.setting is None")

        protocol = "ws://"

        if self.settings.SCHEME == "https":
            protocol = "wss://"

        return protocol + self.settings.MATTERMOST_URL + ":" + \
            str(self.settings.MATTERMOST_PORT) + \
            self.settings.MATTERMOST_API_PATH + "/websocket"

    def send_typing(self, ws: websocket.WebSocket):
        """
        Notify that the bot is typing.
        """

        ws.send(json.dumps(self.websocket_typing))
        if self.is_typing:
            threading.Timer(1.0, self.send_typing, args=[ws]).start()
        else:
            ws.close()


if __name__ == "__main__":
    bot = Bot(settings=Settings(), plugins=[ChatBot()])
    bot.run()
