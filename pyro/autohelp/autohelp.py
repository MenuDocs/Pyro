import asyncio
import datetime
import difflib
import itertools
import logging
import time
from typing import Callable, List, Optional, Tuple, Type, TypedDict

import libcst
import nextcord
from bot_base.caches import TimedCache
from pyro import checks
from pyro.autohelp import AUTO_HELP_CONF, CodeBinExtractor, Conf
from pyro.autohelp.regexes import (
    FORMATTED_CODE_REGEX,
)

from .ast_visitor import (
    Actions,
    BaseHelpTransformer,
    CallbackRequiresSelfVisitor,
    ClientIsNotBot,
    EventListenerVisitor,
    FindPassContext,
    IncorrectTypeHints,
    ProcessCommandsTransformer,
)

log = logging.getLogger(__name__)


class Field(TypedDict):
    name: str
    value: str
    inline: bool


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
                    checks.AUTO_HELP_ROLES.get(interaction.channel.guild.id) or set()
                )
            )
            or interaction.user.id == self._author_id
            or interaction.user.id in checks.COMBINED_ACCOUNTS
        )


class AutoHelp:
    def __init__(self, bot):
        self.bot = bot
        self._help_cache: TimedCache = TimedCache()

        self.actions = {
            Actions.CLIENT_IS_NOT_BOT: self.client_bot,
            Actions.DECORATOR_EVENT_CALLED: self.events_dont_use_brackets,
            Actions.USING_SELF_ON_BOT_COMMAND: self.requires_self_removal,
            Actions.PROCESS_COMMANDS_NOT_CALLED: self.on_message_without_process_commands,
            Actions.MISSING_SELF_IN_EVENT_OR_COMMAND: self.requires_self_addition,
            Actions.INCORRECT_CTX_TYPEHINT: self.invalid_ctx_typehint,
            Actions.INCORRECT_INTERACTION_TYPEHINT: self.invalid_interaction_typehint,
            Actions.USED_PASS_CONTEXT: self.pass_context,
        }

        self.visitors: list[Type[BaseHelpTransformer]] = [
            EventListenerVisitor,
            ClientIsNotBot,
            ProcessCommandsTransformer,
            CallbackRequiresSelfVisitor,
            IncorrectTypeHints,
            FindPassContext,
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
        self,
        message: nextcord.Message,
        original_code: List[str],
        updated_code: List[str],
    ) -> Tuple[nextcord.Embed, Tuple[Field, Field]]:
        embed = nextcord.Embed(
            timestamp=message.created_at,
            color=self.color,
        )
        embed.set_author(
            name="Pyro Auto Helper", icon_url=message.guild.me.display_avatar.url
        )
        embed.set_footer(
            text="Believe this is incorrect? Let Skelmis know in discord.gg/menudocs"
        )
        original_code = "```py\n" + "\n``````py\n".join(original_code) + "\n```"
        updated_code = "```py\n" + "\n``````py\n".join(updated_code) + "\n```"
        return embed, (
            Field(name="Old code", value=original_code),
            Field(name="New | Fixed", value=updated_code),
        )

    async def find_code(self, message: nextcord.Message) -> Optional[List[str]]:
        """
        Parses the code out of the passed message.

        Returns None if no code is found.
        """
        code = []
        paste_code = await self._code_bin.process(message.content)

        if matches := list(FORMATTED_CODE_REGEX.finditer(message.content)):
            for match in matches:
                if not match.group("block"):
                    continue
                code.append(match.group("code"))
        else:
            code.append(message.content)

        if paste_code:
            code.append(paste_code)

        return code or None

    async def process_message(
        self, message: nextcord.Message
    ) -> Optional[List[nextcord.Embed]]:
        # Don't help people who have been helped in the last 5 minutes
        key = f"{message.author.id}|{message.channel.id}"
        if key in self._help_cache:
            return None

        contents = await self.find_code(message)
        if not contents:
            return

        # parse the contents
        # test the first valid code snippet for now
        total_old = ''
        total_new = ''
        errors = []
        # attempt to parse the full code
        for num , code in enumerate(['\n'.join(contents),*contents]):
            try:
                parsed = libcst.parse_module(code)
            except libcst.ParserSyntaxError:
                continue
            results = parsed
            total_old += parsed.code + '\n'
            visitors: list[libcst.CSTTransformer] = []
            local_errors = []
            for visitor in self.visitors:
                visitor = visitor()
                visitors.append(visitor)
                results = results.visit(visitor)
                if visitor.found_errors:
                    local_errors.extend(visitor.found_errors)

            total_new += results.code + '\n'
            if local_errors:
                errors.extend(local_errors)

            if num == 0:
                # stop short if we're running all code blocks successfully
                break

        if not errors:
            return None

        errors = set(errors)
        actions = []
        original_code = parsed.code
        new_code = total_new

        original_code_split = original_code.splitlines(keepends=True)
        new_code_split = new_code.splitlines(keepends=True)
        original_code = []
        new_code = []

        for diff in difflib.unified_diff(original_code_split, new_code_split, n=1):
            if diff.startswith("@@"):
                original_code.append("")
                new_code.append("")
            elif diff.strip() in ("+++", "---"):
                continue
            elif diff.startswith("+"):
                new_code[-1] += diff[1:]
            elif diff.startswith("-"):
                original_code[-1] += diff[1:]
            elif diff.startswith(" "):
                original_code[-1] += diff[1:]
                new_code[-1] += diff[1:]

        for error, action in self.actions.items():
            if error in errors:
                actions.append(action(message))
        embed, last_fields = self.build_embed(message, original_code, new_code)

        fields = list(filter(None, await asyncio.gather(*actions)))

        if original_code != new_code:
            all_fields = [*fields, *last_fields]
        else:
            all_fields = [*fields]

        for field in all_fields:
            if field.get("inline") is None:
                field["inline"] = False

            embed.add_field(**field)

        # self._help_cache.add_entry(key, None, ttl=datetime.timedelta(minutes=30))

        auto_message = await message.channel.send(
            f"{message.author.mention} {'this' if len(fields) == 1 else 'these'} might help.",
            embed=embed,
        )

        await auto_message.edit(view=CloseButton(auto_message, message.author))

    async def events_dont_use_brackets(self, message: nextcord.Message) -> Field:
        return Field(
            name="Events don't use brackets",
            value="When defining an event you do not need to use `()`.\n"
            "See below for how to fix this.",
        )

    async def on_message_without_process_commands(
        self, message: nextcord.Message
    ) -> Field:
        conf: Conf = self.get_conf(message.guild.id)
        return Field(
            name="Overriding on_message without process_commands",
            value=(
                "Looks like you override the `on_message` event "
                "without processing commands.\n This means your commands "
                "will not get called at all, you should change your event to the below.\n"
                "*Note: This may not be in the right place so double check it is.*\n"
                f"You can read more about it [here]({conf.on_message_process_commands_link})"
            ),
        )

    async def invalid_ctx_typehint(self, message: nextcord.Message) -> Field:

        conf: Conf = self.get_conf(message.guild.id)

        return Field(
            name="Incorrect context typehint",
            value=(
                "Looks like you're using a prefix command, but type-hinted the main parameter "
                "incorrectly! This won't lead to errors but will seriously hinder your "
                f"development. See more about contexts [here]({conf.context_link})"
            ),
        )

    async def invalid_interaction_typehint(self, message: nextcord.Message) -> Field:
        conf: Conf = self.get_conf(message.guild.id)

        return Field(
            name="Incorrect interaction typehint",
            value=(
                "Looks like you're using a application command, but type-hinted the main parameter "
                "incorrectly! This won't lead to errors but will seriously hinder your "
                f"development. See more about interactions [here]({conf.interaction_link})"
            ),
        )

    async def client_bot(self, message: nextcord.Message) -> Field:
        """Checks good naming conventions"""
        return Field(
            name="Calling a `Bot` `client` is not recommended.",
            value="Read [here](https://tutorial.vcokltfre.dev/tips/clientbot/) for more detail.\n\n",
        )

    async def pass_context(self, message: nextcord.Message) -> Field:
        """Checks, and notifies if people use pass_context"""
        # Lol, cmon
        return Field(
            name="pass_context is no longer supported.",
            value="Looks like you're still using `pass_context`. That was a feature "
            "back in version 0.x.x five years ago, you're likely using a fork of the now "
            "no longer maintained discord.py which means you're on version "
            "2.x.x.\nPlease check where you're getting this code from and read "
            "your fork's migration guides.",
        )

    async def requires_self_removal(self, message) -> Field:
        """
        Look in a message and attempt to auto-help on
        instances where members send code NOT in a cog
        that also contains self
        """
        return Field(
            name="Commands/events in the global scope don't take self",
            value="Looks like you're defining a command/self with `self` as the first argument "
            "without using the correct decorator. Likely you want to remove `self` as this only "
            "applies to method defined within a class (Cog).",
        )

    async def requires_self_addition(self, message) -> Field:
        """
        Look in a message and attempt to auto-help on
        instances where members send code IN a cog
        that doesnt contain self
        """
        return Field(
            name="Missing self param.",
            value="Looks like you're defining an event or command in a class (Cog) without "
            "using `self` as the first variable.\nThis will likely lead to issues and "
            "you should change it as per the below:",
        )
