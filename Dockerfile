FROM python:3.10-slim

ENV BOT_TOKEN=""
ENV WP_BASE=""
ENV WP_USER=""
ENV WP_PASS=""

RUN adduser faqbot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY faqbot /src/

USER faqbot

CMD [ "/usr/local/bin/python" , "/src/faqbot.py"]