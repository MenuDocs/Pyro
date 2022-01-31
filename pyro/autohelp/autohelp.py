import asyncio
import itertools
import logging
from typing import Callable, Optional, List

import nextcord

from pyro import checks
from pyro.autohelp import CodeBinExtractor, Conf, AUTO_HELP_CONF
from pyro.autohelp.regexes import (
    requires_self_removal_pattern,
    event_requires_self_addition_pattern,
    command_requires_self_addition_pattern,
    command_pass_context_pattern,
    invalid_ctx_or_inter_type_pattern,
    client_bot_pattern,
    on_message_without_process_commands,
    events_dont_use_brackets,
)

log = logging.getLogger(__name__)

MENUDOCS = 416512197590777857
NEXTCORD = 881118111967883295
DISNAKE = 808030843078836254
AUTO_HELP_ROLES = {
    MENUDOCS: {
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


class CloseButton(nextcord.ui.View):
    def __init__(
        self,
        message: nextcord.Message,
        actual_author: nextcord.Member,
    ) -> None:
        super().__init__(timeout=None)
        self._message = message
        self._author_id = actual_author.id
        self._allowed_roles = {role.id for role in actual_author.roles}

    @nextcord.ui.button(label="🚮 Delete this message", style=nextcord.ButtonStyle.red)
    async def close_button(
        self, button: nextcord.Button, interaction: nextcord.Interaction
    ):
        await self._message.delete()

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return (
            bool(
                self._allowed_roles.intersection(
                    AUTO_HELP_ROLES[interaction.channel.guild.id]
                )
            )
            or interaction.user.id == self._author_id
            or interaction.user.id in checks.COMBINED_ACCOUNTS
        )


class AutoHelp:
    def __init__(self, bot):
        self.requires_self_removal = requires_self_removal_pattern
        self.event_requires_self_addition = event_requires_self_addition_pattern
        self.command_requires_self_addition = command_requires_self_addition_pattern
        self.command_pass_context = command_pass_context_pattern
        self.invalid_ctx_or_inter_type = invalid_ctx_or_inter_type_pattern
        self.client_bot = client_bot_pattern
        self.on_message_without_process_commands = on_message_without_process_commands
        self.events_dont_use_brackets = events_dont_use_brackets

        self.patterns: List[Callable] = [
            self.process_requires_self_removal,
            self.process_requires_self_addition,
            self.process_invalid_ctx_or_inter_type,
            self.process_client_bot,
            self.process_pass_context,
            self.process_events_dont_use_brackets,
            self.process_on_message_without_process_commands,
        ]

        # Settings
        self.color = 0x26F7FD
        self._code_bin: CodeBinExtractor = CodeBinExtractor(bot)

    @staticmethod
    def get_conf(guild_id: int) -> Conf:
        try:
            return AUTO_HELP_CONF[guild_id]
        except KeyError:
            return AUTO_HELP_CONF[-1]

    def build_embed(
        self, message: nextcord.Message, description: str
    ) -> nextcord.Embed:
        embed = nextcord.Embed(
            description=description,
            timestamp=message.created_at,
            color=self.color,
        )
        embed.set_author(
            name="Pyro Auto Helper", icon_url=message.guild.me.display_avatar.url
        )
        embed.set_footer(
            text="Believe this is incorrect? Let Skelmis know in discord.gg/menudocs"
        )
        return embed

    async def process_message(
        self, message: nextcord.Message
    ) -> Optional[List[nextcord.Embed]]:
        code_bin_content = await self._code_bin.process(message.content)
        message.content += code_bin_content
        message.content = message.content = message.content.replace("\r", "")

        iters = [call(message) for call in self.patterns]
        results = await asyncio.gather(*iters)
        results = list(filter(None, results))
        if not results:
            return None

        auto_message = await message.channel.send(
            f"{message.author.mention} {'this' if len(results) == 1 else 'these'} might help.",
            embeds=results,
        )

        await auto_message.edit(view=CloseButton(auto_message, message.author))

    async def process_events_dont_use_brackets(self, message: nextcord.Message):
        events_dont_use_brackets_found = self.events_dont_use_brackets.search(
            message.content
        )
        if not events_dont_use_brackets_found:
            return None

        old = events_dont_use_brackets_found.group("all")
        the_rest = events_dont_use_brackets_found.group("the_rest")
        instance_name = events_dont_use_brackets_found.group("instance_name")

        fixed = f"@{instance_name}.event"
        return self.build_embed(
            message,
            description="When defining an event you do not need to use `()`.\n"
            "See below for how to fix this:"
            f"\n\n**Old**\n```py\n{old}{the_rest}```\n**New | Fixed**\n```py\n{fixed}{the_rest}```",
        )

    async def process_on_message_without_process_commands(
        self, message: nextcord.Message
    ):
        on_message_without_process_commands_found = (
            self.on_message_without_process_commands.search(message.content)
        )
        if on_message_without_process_commands_found is None:
            return None

        old_code = on_message_without_process_commands_found.group("code")
        if "process_commands" in old_code:
            return None

        args = on_message_without_process_commands_found.group("args")
        instance_name = on_message_without_process_commands_found.group("instance_name")

        indent = sum(1 for _ in itertools.takewhile(str.isspace, str(old_code))) * " "

        conf: Conf = self.get_conf(message.guild.id)

        base = f"@{instance_name}.event\nasync def on_message({args}):\n{old_code}"
        code = f"{base}\n{indent}await {instance_name}.process_commands({args})"
        output = (
            "Looks like you override the `on_message` event "
            "without processing commands.\n This means your commands "
            "will not get called at all, you should change your event to the below."
            f"\n\n**Old**\n```py\n{base}```\n**New | Fixed**\n```py\n{code}```\n\n"
            f"Note: This may not be in the right place so double check it is.\n"
            f"You can read more about it [here]({conf.on_message_process_commands_link})"
        )

        if len(code.split("\n")) > 10:
            # Too big for one embed
            output = (
                "Looks like you override the `on_message` event "
                "without processing commands.\n This means your commands "
                "will not get called at all, you should make sure to add "
                f"`await {instance_name}.process_commands({args})` into your `on_message` event.\n"
                f"You can read more about it [here]({conf.on_message_process_commands_link})"
            )

        return self.build_embed(message, description=output)

    async def process_invalid_ctx_or_inter_type(
        self, message: nextcord.Message
    ) -> Optional[nextcord.Embed]:
        invalid_ctx_or_inter_type = self.invalid_ctx_or_inter_type.search(
            message.content
        )
        if invalid_ctx_or_inter_type is None:
            return None

        conf: Conf = self.get_conf(message.guild.id)
        arg_type = invalid_ctx_or_inter_type.group("arg_type")
        command_type = invalid_ctx_or_inter_type.group("command_type")
        all_params = old_all_params = invalid_ctx_or_inter_type.group("all")

        if command_type == "command" and "interaction" in arg_type.lower():
            # Replace interaction with ctx
            new_arg_type = " commands.Context"
            notes = (
                "Make sure to `from nextcord.ext import commands`.\n"
                "You can read more about `Context` "
                f"[here]({conf.context_link})"
            )
            all_params = all_params.replace(arg_type, new_arg_type)

        elif command_type != "command" and "context" in arg_type.lower():
            new_arg_type = " nextcord.Interaction"
            notes = (
                "Make sure to `import nextcord`.\n"
                "You can read more about `Interaction` "
                f"[here]({conf.interaction_link})"
            )
            all_params = all_params.replace(arg_type, new_arg_type)

        else:
            log.warning("Idk how I got here.")
            return None

        return self.build_embed(
            message,
            description=f"Looks like you're using a command, but type-hinted the main parameter "
            f"incorrectly! This won't lead to errors but will seriously hinder your "
            f"development."
            f"\n\n**Old**\n```py{old_all_params}```\n**New | Fixed**\n```py{all_params}```\n\nNotes: {notes}",
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
            description=f"Calling a `Bot`, `{client_bot.group('name')}` is not recommended.\n"
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
            description="Looks like you're using `pass_context` still. That was a feature "
            "back in version 0.x.x five years ago, your likely using a fork of the now "
            "no longer maintained discord.py which means your on version "
            "2.x.x.\nPlease check where your getting this code from and read "
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

        if injected_self.group("var") == "commands":
            return

        initial_func = injected_self.group("func")
        fixed_func = initial_func.replace("self,", "")
        if "( c" in fixed_func:
            fixed_func = fixed_func.replace("( c", "(c")

        # We need to process this
        return self.build_embed(
            message,
            description="Looks like you're defining a command with `self` as the first argument "
            "without using the correct decorator. Likely you want to remove `self` as this only "
            "applies to commands defined within a class (Cog).\nYou should change it as per the following:"
            f"\n\n**Old**\n```py{initial_func}```\n**New | Fixed**\n```py{fixed_func}```",
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
            description=f"Looks like you're defining {msg} in a class (Cog) without "
            "using `self` as the first variable.\nThis will likely lead to issues and "
            "you should change it as per the following:"
            f"\n\n**Old**\n```py{initial_func}```\n**New | Fixed**\n```py{final_func}```",
        )
