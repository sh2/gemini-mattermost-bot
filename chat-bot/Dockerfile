FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY gemini-chat-bot.py requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt
CMD ["python", "gemini-chat-bot.py"]