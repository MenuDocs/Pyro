import asyncio
import io
import os
import re
import signal

import dotenv
import logging
import textwrap
import contextlib
from traceback import format_exception

import aiohttp
import disnake
from alaric import AQ
from alaric.comparison import EQ
from bot_base import BotContext
from bot_base.paginators.disnake_paginator import DisnakePaginator
from disnake.ext import commands
from disnake.ext import tasks

from pyro import checks
from pyro.bot import Pyro
from pyro.checks import COMBINED_ACCOUNTS
from pyro.utils.util import clean_code

dotenv.load_dotenv()

mongo_url = os.getenv("MONGO")
token = os.getenv("TOKEN")
patch = os.getenv("UPTIME_PATCH")


logging.basicConfig(
    format="%(levelname)-7s | %(asctime)s | %(filename)12s:%(funcName)-12s | %(message)s",
    datefmt="%I:%M:%S %p %d/%m/%Y",
    level=logging.INFO,
)
gateway_logger = logging.getLogger("disnake.gateway")
gateway_logger.setLevel(logging.WARNING)
client_logger = logging.getLogger("disnake.client")
client_logger.setLevel(logging.WARNING)

intents = disnake.Intents.all()


async def main():
    bot = Pyro(
        case_insensitive=True,
        description="A short sharp bot coded in python to aid the python "
        "developers with helping the community "
        "with nextcord related issues.",
        intents=intents,
        mongo_url=mongo_url,
        leave_db=True,
        command_prefix="py.",
        load_builtin_commands=True,
        activity=disnake.Game(name="All new and improved"),
    )

    logger = logging.getLogger(__name__)

    # Use regex to parse mentions, much better than only supporting
    # nickname mentions (<@!1234>)
    # This basically ONLY matches a string that only consists of a mention
    mention = re.compile(r"^<@!?(?P<id>\d+)>$")

    @bot.event
    async def on_ready():
        logger.info("I'm all up and ready like mom's spaghetti %s")

    @bot.event
    async def on_message(message: disnake.Message):
        if bot.is_debug_mode and message.author.id not in COMBINED_ACCOUNTS:
            # During dev only run commands from us so as to not impact the end user
            return

        # Ignore messages sent by bots
        if message.author.bot:
            return

        # Whenever the bot is tagged, respond with its prefix
        if match := mention.match(message.content):
            if int(match.group("id")) == bot.user.id:
                data = await bot.db.config.find(AQ(EQ("_id", message.guild.id)))
                if not data or "prefix" not in data:
                    prefix = bot.DEFAULT_PREFIX
                else:
                    prefix = data["prefix"]

                await message.channel.send(
                    f"My prefix here is `{prefix}`", delete_after=15
                )

        await bot.process_commands(message)

    @bot.command(description="Log the bot out.")
    @commands.is_owner()
    async def logout(ctx):
        await ctx.send("Cya :wave:")
        await bot.graceful_shutdown()

    @bot.command(name="eval", aliases=["exec"])
    @checks.can_eval()
    async def _eval(ctx, *, code):
        """
        Evaluates given code.
        """
        code = clean_code(code)

        local_variables = {
            "disnake": disnake,
            "commands": commands,
            "bot": bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}",
                    local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"

        except Exception as e:
            result = "".join(format_exception(type(e), e, e.__traceback__))

        async def format_page(code, page_number):
            embed = disnake.Embed(title=f"Eval for {ctx.author.name}")
            embed.description = f"```{code}```"

            embed.set_footer(text=f"Page {page_number}")
            return embed

        paginator: DisnakePaginator = DisnakePaginator(
            1,
            [result[i : i + 2000] for i in range(0, len(result), 2000)],
        )
        paginator.format_page = format_page
        await paginator.start(context=ctx)

    @bot.command()
    @checks.can_eval()
    async def note(ctx: BotContext, *, note: str):
        channel = await bot.get_or_fetch_channel(702862760052129822)
        await channel.send(
            embed=disnake.Embed(
                title=f"Note for {ctx.author.name}",
                description=f"{note}\n\n[Jump to]({ctx.message.jump_url})",
            )
        )
        await ctx.send("Made a note of it.")

    @bot.command()
    @checks.can_eval()
    async def process(ctx, msg: disnake.Message):
        msg.channel = ctx.channel
        await bot.auto_help.process_message(msg)

    @tasks.loop(seconds=30)
    async def update_uptime():
        if patch:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=f"https://status.koldfusion.xyz/api/push/{patch}?status=up&msg=OK&ping="
                ):
                    pass

    @update_uptime.before_loop
    async def before_update_uptime():
        await bot.wait_until_ready()

    async def graceful_shutdown(b: Pyro, sig_name):
        await b.graceful_shutdown()

    # https://github.com/gearbot/GearBot/blob/live/GearBot/GearBot.py#L206-L212
    try:
        for signature in ("SIGINT", "SIGTERM", "SIGKILL"):
            asyncio.get_event_loop().add_signal_handler(
                getattr(signal, signature),
                lambda: asyncio.ensure_future(graceful_shutdown(bot, signature)),
            )
    except Exception as e:
        pass  # doesn't work on Windows

    update_uptime.start()
    async with aiohttp.ClientSession() as session:
        bot.session = session
        await bot.load()
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
