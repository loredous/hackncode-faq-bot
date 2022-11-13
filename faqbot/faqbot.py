import datetime
import os
import typing
from xmlrpc.client import Fault

import discord
from discord.ext import commands
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import EditPost, GetPost, NewPost

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

# WP Setup
wp_client = Client(f'{os.getenv("WP_BASE")}/xmlrpc.php',
                   os.getenv('WP_USER'), os.getenv('WP_PASS'))


@bot.slash_command(name="postcreate", description="Create a new post based on an existing message")
async def create_post(ctx, message: discord.Message, title: typing.Optional[str] = None):
    if not title:
        title = f"Bot Generated from {ctx.user.display_name} in {ctx.channel.name} on {str(datetime.datetime.now())}"
    new_post = WordPressPost()
    new_post.title = title
    new_post.content = message.content
    id = wp_client.call(NewPost(new_post))
    await ctx.respond(f'Message saved as Post ID {id}!')


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

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN", None))
