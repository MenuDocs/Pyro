import re

"""Pastebin Regexs"""
vco_cf_worker_boi: re.Pattern = re.compile(
    r"https://(?P<url>paste.(nextcord|disnake).dev)/?\?(language=python&)?(id=(?P<id>[0-9]*))?"
)

"""If you override it, make sure to process commands"""
on_message_without_process_commands = re.compile(
    r"@(?P<instance_name>[a-zA-Z0-9_]*?)\.event\nasync def on_message"
    r"\((?P<args>[a-zA-Z0-9_]*?)\):\n((?P<indent>\s+)"
    r"(?P<initial_code>[a-zA-Z0-9_ ().=!*&^%$#@:])+)(\s)?"
    r"(?P<code>(\s+([a-zA-Z0-9_ ().=!*&^%$#@:])+)+)?(\s)?"
)

"""Remove self from all command types if not in a class"""
requires_self_removal_pattern: re.Pattern = re.compile(
    r"@(?P<var>[a-zA-Z0-9_]*?)\.(command|slash_command|user_command|message_command)"
    r"\([a-zA-Z= _]*?\)\n\s{0,8}((?P<func>async def .*\(self,\s*?ctx.*\)):)",
)
# TODO Add events

"""Add self to all command types and cog listeners if required"""
command_requires_self_addition_pattern: re.Pattern = re.compile(
    r"@((commands\.)?command|(nextcord\.)?(slash_command|user_command|message_command))"
    r"\([a-zA-Z= _]*?\)\n\s{0,8}(?P<def>async def .*\()(?P<func>.*)(?P<close>\).*:)"
)
event_requires_self_addition_pattern: re.Pattern = re.compile(
    r"@commands\.Cog\.listener\(\)\n\s{0,8}(?P<def>async def .*\()(?P<func>.*)(?P<close>\).*:)"
)

"""Stop using outdated features"""
command_pass_context_pattern: re.Pattern = re.compile(
    r"@([a-zA-Z0-9_]*?)\.command\(\s*?pass_context\s*?=\s*?True\)"
)

"""Follow some practices"""
client_bot_pattern: re.Pattern = re.compile(
    r"(?P<name>(?i:client))\s*?=\s*?commands.Bot"
)

"""Invalid typehint for command type"""
invalid_ctx_or_inter_type_pattern: re.Pattern = re.compile(
    r"@((?P<cog>[a-zA-Z0-9_]*?|commands)\.)?"
    r"(?P<command_type>command|slash_command|user_command|message_command)"
    r"\([a-zA-Z= _]*?\)\n\s{0,8}(async def .*\()(?P<all>(self,\s*)?"
    r"((?P<arg>[a-zA-Z_\s]+):(?P<arg_type>[a-zA-Z\s\.]+))(.*))(\).*:)"
)
