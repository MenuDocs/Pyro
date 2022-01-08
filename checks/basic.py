from nextcord.ext import commands

SKELMIS_ACCOUNTS = {
    271612318947868673,  # Skelmis
    493937661044719626,  # Its Dave
}
AUXTAL_ACCOUNTS = {
    327745755789918208,  # Auxtal
}

COMBINED_ACCOUNTS = set.union(SKELMIS_ACCOUNTS, AUXTAL_ACCOUNTS)


def can_eval():
    async def _check(ctx):
        if ctx.author.id in COMBINED_ACCOUNTS:
            return True

        raise commands.NotOwner

    return commands.check(_check)
