import re

"""Remove self from all command types if not in a class"""
requires_self_removal_pattern: re.Pattern = re.compile(
    r"@[a-zA-Z0-9_]*?\.(command|slash_command|user_command|message_command)"
    r"\([a-zA-Z= _]*?\)\n\s{0,8}(async def .*\((?P<func>self,\s*?ctx.*)\):)",
)

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
    r"@commands\.command\(\s*?pass_context\s*?=\s*?True\)"
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
