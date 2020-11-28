import json

import discord
from aiohttp import ClientSession
from discord.ext.buttons import Paginator


class Pag(Paginator):
    async def teardown(self):
        try:
            await self.page.clear_reactions()
        except discord.HTTPException:
            pass


def clean_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```py\n```
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    else:
        return content


async def get_jwt():
    with open("config.json", "r") as f:
        config = json.load(f)

    params = {"identifier": config["API_username"], "password": config["API_password"]}

    async with ClientSession() as session:
        async with session.post(
            "https://menudocs-admin.herokuapp.com/auth/local", data=params
        ) as response:
            r = await response.json()
            return r["jwt"]
