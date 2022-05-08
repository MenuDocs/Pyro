from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands

if TYPE_CHECKING:
    from pyro import Pyro
    from bot_base import BotContext
    from bot_base.wraps import WrappedMember

SKELMIS_ACCOUNTS = {
    271612318947868673,  # Skelmis
    493937661044719626,  # Its Dave
}
AUXTAL_ACCOUNTS = {
    327745755789918208,  # Auxtal
}

MAIN_GUILD = 416512197590777857
PROJECT_GUILD = 566131499506860045
AUXTAL_TESTING_GUILD = 888614043433197568
MENUDOCS_GUILD_IDS = {MAIN_GUILD, PROJECT_GUILD, AUXTAL_TESTING_GUILD}
MENUDOCS_SUGGESTIONS_CHANNEL = 516060828412280852  # suggestions
PYTHON_HELP_CHANNEL_IDS = {
    621912956627582976,  # discord.py
    621913007630319626,  # python
    702862760052129822,  # pyro
    416522595958259713,  # commands (main dc)
    888614043835830300,  # Auxtal testing channel
}
CODE_REVIEWER, PROFICIENT, TEAM = {
    850330300595699733,  # Code Reviewer
    479199775590318080,  # Proficient
    659897739844517931,  # ⚔ Team
}
NEXTCORD = 881118111967883295
NEXTCORD_ID = {NEXTCORD}
NEXTCORD_ALLOWED_AUTOHELP_CHANNELS = {
    881118112492191796,  # general
    881965127031722004,  # help
    881135921276272670,  # commands
}
DISNAKE = 808030843078836254
DISNAKE_ID = {DISNAKE}
DISNAKE_ALLOWED_AUTOHELP_CHANNELS = {
    883342278280745030,  # help-disnake
    925508492574474270,
}

ALLOWED_HELP_CHANNELS = set.union(
    PYTHON_HELP_CHANNEL_IDS,
    NEXTCORD_ALLOWED_AUTOHELP_CHANNELS,
    DISNAKE_ALLOWED_AUTOHELP_CHANNELS,
)
AUTO_HELP_ROLES = {
    MAIN_GUILD: {
        479199775590318080,  # Proficient
    },
    NEXTCORD: {
        882192899519954944,  # Help thread auto add
    },
    DISNAKE: {
        891619545356308481,  # Collaborator
        922539851667091527,  # Smol mod
        808033337767362570,  # Mod
        847846236555968543,  # Solid contrib
    },
}

AUTOHELP_ALLOWED_DISCORDS = set.union(MENUDOCS_GUILD_IDS, NEXTCORD_ID, DISNAKE_ID)
COMBINED_ACCOUNTS = set.union(SKELMIS_ACCOUNTS, AUXTAL_ACCOUNTS)


def can_eval():
    async def _check(ctx):
        if ctx.author.id in COMBINED_ACCOUNTS:
            return True

        raise commands.NotOwner

    return commands.check(_check)


def ensure_is_menudocs_guild():
    async def check(ctx):
        if not ctx.guild or ctx.guild.id not in MENUDOCS_GUILD_IDS:
            return False
        return True

    return commands.check(check)


def ensure_is_menudocs_project_guild():
    async def check(ctx):
        if not ctx.guild or ctx.guild.id != PROJECT_GUILD:
            return False
        return True

    return commands.check(check)


def ensure_is_menudocs_staff():
    async def check(ctx: "BotContext"):
        bot: "Pyro" = ctx.bot  # type: ignore
        guild: disnake.Guild = await bot.get_or_fetch_guild(MAIN_GUILD)

        try:
            main_guild_member: "WrappedMember" = await bot.get_or_fetch_member(
                MAIN_GUILD, ctx.author.id
            )
        except disnake.DiscordException:
            return False

        team = guild.get_role(TEAM)
        proficient = guild.get_role(PROFICIENT)
        code_reviewer = guild.get_role(CODE_REVIEWER)

        return (
            team in main_guild_member.roles
            or proficient in main_guild_member.roles
            or code_reviewer in main_guild_member.roles
        )

    return commands.check(check)
