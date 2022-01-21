from nextcord.ext import commands

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
NEXTCORD_ID = {881118111967883295}
NEXTCORD_ALLOWED_AUTOHELP_CHANNELS = {
    881118112492191796,  # general
    881965127031722004,  # help
}
DISNAKE_ID = {808030843078836254}
DISNAKE_ALLOWED_AUTOHELP_CHANNELS = {
    883342278280745030,  # help-disnake
}

ALLOWED_HELP_CHANNELS = set.union(
    PYTHON_HELP_CHANNEL_IDS,
    NEXTCORD_ALLOWED_AUTOHELP_CHANNELS,
    DISNAKE_ALLOWED_AUTOHELP_CHANNELS,
)
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
    async def check(ctx):
        if not commands.has_any_role(CODE_REVIEWER, PROFICIENT, TEAM):
            return False
        return True

    return commands.check(check)
