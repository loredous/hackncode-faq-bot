import typing
import discord
from discord.ext import commands
import os
import datetime

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost


# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

# WP Setup
wp_client = Client(f'{os.getenv("WP_BASE")}/xmlrpc.php',
                   os.getenv('WP_USER'), os.getenv('WP_PASS'))


@bot.slash_command(name="savemessage")
async def add_faq(ctx, message: discord.Message, title: typing.Optional[str] = None):
    if not title:
        title = f"Bot Generated from {ctx.user.display_name} in {ctx.channel.name} on {str(datetime.datetime.now())}"
    new_post = WordPressPost()
    new_post.title = title
    new_post.content = message.content
    id = wp_client.call(NewPost(new_post))
    await ctx.respond(f'Message saved as Post ID {id}!')

if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN", None))
