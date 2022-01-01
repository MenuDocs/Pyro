import asyncio
import logging
from typing import Callable, Optional, List

import nextcord

from autohelp.regexes import (
    requires_self_removal,
    event_requires_self_addition,
    command_requires_self_addition,
    command_pass_context,
    invalid_ctx_or_inter_type,
    client_bot,
)

log = logging.getLogger(__name__)


class AutoHelp:
    def __init__(self):
        self.requires_self_removal = requires_self_removal
        self.event_requires_self_addition = event_requires_self_addition
        self.command_requires_self_addition = command_requires_self_addition
        self.command_pass_context = command_pass_context
        self.invalid_ctx_or_inter_type = invalid_ctx_or_inter_type
        self.client_bot = client_bot

        self.patterns: List[Callable] = [
            self.process_requires_self_removal,
            self.process_requires_self_addition,
            self.process_invalid_ctx_or_inter_type,
            self.process_client_bot,
            self.process_pass_context,
        ]

        # Settings
        self.color = 0x26F7FD

    def build_embed(
        self, message: nextcord.Message, description: str
    ) -> nextcord.Embed:
        embed = nextcord.Embed(
            description=description,
            timestamp=message.created_at,
            color=self.color,
        )
        embed.set_author(name="Pyro Auto Helper", icon_url=message.guild.me.avatar.url)
        embed.set_footer(
            text="Believe this is incorrect? Let Skelmis know in discord.gg/menudocs"
        )
        return embed

    async def process_message(self, message: nextcord.Message) -> List[nextcord.Embed]:
        iters = [call(message) for call in self.patterns]
        results = await asyncio.gather(*iters)
        return list(filter(None, results))

    async def process_invalid_ctx_or_inter_type(
        self, message: nextcord.Message
    ) -> Optional[nextcord.Embed]:
        invalid_ctx_or_inter_type = self.invalid_ctx_or_inter_type.search(
            message.content
        )
        if invalid_ctx_or_inter_type is None:
            return None

        arg_type = invalid_ctx_or_inter_type.group("arg_type")
        command_type = invalid_ctx_or_inter_type.group("command_type")
        all_params = old_all_params = invalid_ctx_or_inter_type.group("all")

        if command_type == "command" and "interaction" in arg_type.lower():
            # Replace interaction with ctx
            new_arg_type = " commands.Context"
            notes = (
                "Make sure to `from nextcord.ext import commands`.\n"
                "You can read more about `Context` "
                "[here](https://nextcord.readthedocs.io/en/latest/ext/commands/api.html#nextcord.ext.commands.Context)"
            )
            all_params = all_params.replace(arg_type, new_arg_type)

        elif command_type != "command" and "context" in arg_type.lower():
            new_arg_type = " nextcord.Interaction"
            notes = (
                "Make sure to `import nextcord`.\n"
                "You can read more about `Interaction` "
                "[here](https://nextcord.readthedocs.io/en/latest/api.html#nextcord.Interaction)"
            )
            all_params = all_params.replace(arg_type, new_arg_type)

        else:
            log.warning("Idk how I got here.")
            return None

        return self.build_embed(
            message,
            description=f"Looks like your using a command, but typehinted the main parameter "
            f"incorrectly! This won't lead to errors but will seriously hinder your "
            f"development."
            f"\n\n**Old**\n`{old_all_params}`\n**New | Fixed**\n`{all_params}`\n\nNotes: {notes}",
        )

    async def process_client_bot(
        self, message: nextcord.Message
    ) -> Optional[nextcord.Embed]:
        """Checks good naming conventions"""
        client_bot = self.client_bot.search(message.content)
        if client_bot is None:
            return None

        return self.build_embed(
            message,
            description=f"Calling a `Bot`, `{client_bot.group('name')}` is not recommended. "
            f"Read [here](https://tutorial.vcokltfre.dev/tips/clientbot/) for more detail.",
        )

    async def process_pass_context(
        self, message: nextcord.Message
    ) -> Optional[nextcord.Embed]:
        """Checks, and notifies if people use pass_context"""
        pass_context = self.command_pass_context.search(message.content)
        if pass_context is None:
            return None

        # Lol, cmon
        return self.build_embed(
            message,
            description="Looks like your using `pass_context` still. That was a feature "
            "back in version 0.x.x, your likely using a fork of the now "
            "no longer maintained discord.py which means your on version "
            "2.x.x. Please check where your getting this code from and read "
            "your forks migration guides.",
        )

    async def process_requires_self_removal(self, message) -> Optional[nextcord.Embed]:
        """
        Look in a message and attempt to auto-help on
        instances where members send code NOT in a cog
        that also contains self
        """
        injected_self = self.requires_self_removal.search(message.content)
        if injected_self is None:
            # Don't process
            return

        initial_func = injected_self.group("func")
        fixed_func = initial_func.replace("self,", "")
        if "( c" in fixed_func:
            fixed_func = fixed_func.replace("( c", "(c")

        # We need to process this
        return self.build_embed(
            message,
            description="Looks like your defining a command with `self` as the first argument "
            "without using the correct decorator. Likely you want to remove `self` as this only "
            "applies to commands defined within a class (Cog).\nYou should change it as per the following:"
            f"\n\n**Old**\n`{initial_func}`\n**New | Fixed**\n`{fixed_func}`",
        )

    async def process_requires_self_addition(self, message) -> Optional[nextcord.Embed]:
        """
        Look in a message and attempt to auto-help on
        instances where members send code IN a cog
        that doesnt contain self
        """
        event_requires_self_addition = self.event_requires_self_addition.search(
            message.content
        )
        command_requires_self_addition = self.command_requires_self_addition.search(
            message.content
        )

        if event_requires_self_addition is not None:
            # Event posted, check if it needs self
            to_use_regex = event_requires_self_addition
            msg = "an event"
        elif command_requires_self_addition is not None:
            # Command posted, check if it needs self
            to_use_regex = command_requires_self_addition
            msg = "a command"
        else:
            return None

        args_group = to_use_regex.group("func")
        if args_group.startswith("self"):
            return

        initial_func = (
            to_use_regex.group("def")
            + to_use_regex.group("func")
            + to_use_regex.group("close")
        )

        args_group = f"self, {args_group}"

        final_func = (
            to_use_regex.group("def") + args_group + to_use_regex.group("close")
        )

        # We need to process this
        return self.build_embed(
            message,
            description=f"Looks like your defining {msg} in a class (Cog) without "
            "using `self` as the first variable. This will likely lead to issues and "
            "you should change it as per the following:"
            f"\n\n**Old**\n`{initial_func}`\n**New | Fixed**\n`{final_func}`",
        )
