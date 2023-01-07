import datetime
import os
import typing
import logging
from xmlrpc.client import Fault

import discord
from discord.ext import commands
import openai
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import EditPost, GetPost, NewPost

# Logging Setup
if bool(os.getenv("DEBUG", False)):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FAQBot")


# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

# WP Setup
wp_client = Client(f'{os.getenv("WP_BASE")}/xmlrpc.php',
                   os.getenv('WP_USER'), os.getenv('WP_PASS'))

# ChatGPT Setup
openai.api_key = os.getenv('AI_TOKEN')
ai_models = {
    "davinci": {"engine": "text-davinci-003", "name": "DaVinci", "tokens": 500},
    "curie": {"engine": "text-curie-001", "name": "Curie", "tokens": 1000},
    "babbage": {"engine": "text-babbage-001", "name": "Babbage", "tokens": 1900},
    "ada": {"engine": "text-ada-001", "name": "Ada", "tokens": 1900},
    "codex": {"engine": "code-davinci-002", "name": "Codex", "tokens": 4000}
}


@bot.slash_command(name="postcreate", description="Create a new post based on an existing message")
async def create_post(ctx, message: discord.Message, title: typing.Optional[str] = None):
    try:
        if not title:
            title = f"Bot Generated from {ctx.user.display_name} in {ctx.channel.name} on {str(datetime.datetime.now())}"
        new_post = WordPressPost()
        new_post.title = title
        new_post.content = message.content
        id = wp_client.call(NewPost(new_post))
        await ctx.respond(f'Message saved as Post ID {id}!')
    except Exception as ex:
        logger.exception(ex)


@bot.slash_command(name="postappend", description="Append to an existing post based on an existing message")
async def append_to_post(ctx, id: int, message: discord.Message):
    try:
        post = wp_client.call(GetPost(id))
    except Fault as f:
        if f.faultCode == 404:  # Post not found
            await ctx.respond(f'Post ID {id} was not found.')
            return
    if post.post_status != "draft":  # Post is not a draft
        await ctx.respond(f'Post ID {id} is in status "{post.post_status}", not "draft". Only draft posts can be appended to.')
        return
    post.content += "\n\n"
    post.content += message.content
    wp_client.call(EditPost(id, post))
    await ctx.respond(f'Message content appended to Post ID {id}!')


@bot.slash_command(name="davinci", description="Provide an automated response to a question using the OpenAI DaVinci engine", guild_ids=[135499198865997824])
async def answer_with_davinci(ctx, message):
    await ask_an_ai(ctx, message, model="davinci")


@bot.slash_command(name="curie", description="Provide an automated response to a question using the OpenAI Curie engine", guild_ids=[135499198865997824])
async def answer_with_curie(ctx, message):
    await ask_an_ai(ctx, message, model="curie")


@bot.slash_command(name="babbage", description="Provide an automated response to a question using the OpenAI Babbage engine", guild_ids=[135499198865997824])
async def answer_with_babage(ctx, message):
    await ask_an_ai(ctx, message, model="babbage")


@bot.slash_command(name="ada", description="Provide an automated response to a question using the OpenAI Ada engine", guild_ids=[135499198865997824])
async def answer_with_ada(ctx, message):
    await ask_an_ai(ctx, message, model="ada")


@bot.slash_command(name="codex", description="Provide automated code generation using the OpenAI Codex engine", guild_ids=[135499198865997824])
async def answer_with_codex(ctx, message):
    await ask_an_ai(ctx, message, model="codex")


async def ask_an_ai(ctx, message, model):
    ai = ai_models[model]
    try:
        question = commands.MessageConverter.convert(
            ctx, argument=message).content
    except Exception:
        question = message
    await ctx.respond(f"Let's ask {ai['name']}: '{question}'")
    try:
        answer = openai.Completion.create(
            engine=ai['engine'], prompt=question, max_tokens=ai['tokens'])
        txt = answer.choices[0].text.strip("\n")
        await ctx.respond(f'{ai["name"]} says:\n{txt}')
    except Exception as ex:
        await ctx.respond('Something went wrong....')
        logger.exception(ex)


if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN", None))
