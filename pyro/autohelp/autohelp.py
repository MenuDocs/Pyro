import asyncio
import datetime
import difflib
import logging
import os
from typing import List, Optional, Tuple, Type, TypedDict

import libcst
import disnake
from aegir import Aegir, ParsedData, FormatError
from bot_base.caches import TimedCache
from libcst import ParserSyntaxError

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


class CloseButton(disnake.ui.View):
    def __init__(
        self,
        message: disnake.Message,
        actual_author: disnake.Member,
    ) -> None:
        super().__init__(timeout=None)
        self._message = message
        self._author_id = actual_author.id
        self._allowed_roles = {role.id for role in actual_author.roles}

    @disnake.ui.button(label="🚮 Delete this message", style=disnake.ButtonStyle.red)
    async def close_button(
        self, button: disnake.Button, interaction: disnake.Interaction
    ):
        await self._message.delete()

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        return (
            bool(
                self._allowed_roles.intersection(
                    checks.AUTO_HELP_ROLES.get(interaction.guild_id) or set()
                )
            )
            or interaction.author.id == self._author_id
            or interaction.author.id in checks.COMBINED_ACCOUNTS
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

    async def upload_to_workbin(self, ast: libcst.CSTNode) -> str:
        code = libcst.Module([]).code_for_node(ast)
        res = await self.bot.session.post(  # type: ignore
            url="https://workbin.dev//api/new",
            json={"content": str(code), "language": "python"},
            headers={"Content-Type": "application/json"},
        )
        paste_id = (await res.json())["key"]
        return f"https://workbin.dev//?id={paste_id}&language=python"

    @staticmethod
    def get_conf(guild_id: int) -> Conf:
        try:
            return AUTO_HELP_CONF[guild_id]
        except KeyError:
            return AUTO_HELP_CONF[-1]

    async def build_embed(
        self, message: disnake.Message, errors: List[FormatError]
    ) -> disnake.Embed:
        embed = disnake.Embed(
            timestamp=message.created_at,
            color=self.color,
        )
        embed.set_author(
            name="Pyro Auto Helper", icon_url=message.guild.me.display_avatar.url
        )
        embed.set_footer(
            text="Believe this is incorrect? Let Skelmis know in discord.gg/menudocs"
        )

        data = {
            "created_for": {
                "user_id": message.author.id,
                "last_known_name": message.author.display_name,
            },
            "errors": [],
        }

        for error in errors:
            old_code_link = await self.upload_to_workbin(error.old_cst)
            fixed_code_link = await self.upload_to_workbin(error.fixed_cst)
            data["errors"].append(
                {
                    "title": error.title,
                    "description": error.description,
                    "old_code_link": old_code_link,
                    "fixed_code_link": fixed_code_link,
                }
            )

        r: ClientResponse = await self.bot.session.post(  # type: ignore
            url="https://pyro.koldfusion.xyz/api/cases",
            json=data,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": os.environ["PYRO_API_KEY"],
            },
        )
        assert r.status == 201, "Failed to create new auto-help resource"
        response_data = await r.json()

        embed.description = (
            f"I've noticed this code has some issues and fixed them for you.\n\n"
            f"You can find the fixed code [here]({response_data['view_url']})."
        )

        return embed

    async def find_code(self, message: disnake.Message) -> Optional[List[str]]:
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
        self, message: disnake.Message
    ) -> Optional[disnake.Embed]:

        key = f"{message.author.id}|{message.channel.id}"
        contents = await self.find_code(message)
        if not contents or key in self._help_cache:
            return None

        # self._help_cache.add_entry(
        #     key,
        #     None,
        #     ttl=datetime.timedelta(minutes=5),
        # )

        sources: List[FormatError] = []
        for code in contents:
            try:
                parsed_data: ParsedData = Aegir.convert_source(code)
            except ParserSyntaxError:
                continue

            sources.extend(parsed_data.errors)

        if not sources:
            return None

        embed = await self.build_embed(message, sources)

        try:
            auto_message = await message.reply(
                f"{message.author.mention} {'this' if len(sources) == 1 else 'these'} might help.",
                embed=embed,
            )
        except disnake.Forbidden:
            log.warning(
                "Failed to send a message to Channel(id=%s, name=%s) as I lack permissions",
                message.channel.id,
                message.channel.name,
            )
            return

        await auto_message.edit(view=CloseButton(auto_message, message.author))

        return embed

    async def events_dont_use_brackets(self, message: disnake.Message) -> Field:
        return Field(
            name="Events don't use brackets",
            value="When defining an event you do not need to use `()`.\n"
            "See below for how to fix this.",
        )

    async def on_message_without_process_commands(
        self, message: disnake.Message
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

    async def invalid_ctx_typehint(self, message: disnake.Message) -> Field:

        conf: Conf = self.get_conf(message.guild.id)

        return Field(
            name="Incorrect context typehint",
            value=(
                "Looks like you're using a prefix command, but type-hinted the main parameter "
                "incorrectly! This won't lead to errors but will seriously hinder your "
                f"development. See more about contexts [here]({conf.context_link})"
            ),
        )

    async def invalid_interaction_typehint(self, message: disnake.Message) -> Field:
        conf: Conf = self.get_conf(message.guild.id)

        return Field(
            name="Incorrect interaction typehint",
            value=(
                "Looks like you're using a application command, but type-hinted the main parameter "
                "incorrectly! This won't lead to errors but will seriously hinder your "
                f"development. See more about interactions [here]({conf.interaction_link})"
            ),
        )

    async def client_bot(self, message: disnake.Message) -> Field:
        """Checks good naming conventions"""
        return Field(
            name="Calling a `Bot` `client` is not recommended.",
            value="Read [here](https://tutorial.vcokltfre.dev/tips/clientbot/) for more detail.\n\n",
        )

    async def pass_context(self, message: disnake.Message) -> Field:
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
