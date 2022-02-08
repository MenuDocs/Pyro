import re

"""Pastebin Regexs"""
vco_cf_worker_boi: re.Pattern = re.compile(
    r"https://(?P<url>paste.((nextcord|disnake|vcokltfre).dev)|vcokltf.re)/?\?(language=python&)?(id=(?P<id>[0-9]*))?"
)

# codeblock extractor
# thank you, python discord
# originally taken from github.com/python-discord/bot/blob/master/bot/exts/utils/codeblock.py
FORMATTED_CODE_REGEX = re.compile(
    r"(?P<delim>(?P<block>```)|``?)"  # code delimiter: 1-3 backticks; (?P=block) only matches if it's a block
    r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"  # if we're in a block, match optional language (only letters plus newline)
    r"(?:[ \t]*\n)*"  # any blank (empty or tabs/spaces only) lines before the code
    r"(?P<code>.*?)"  # extract all code inside the markup
    r"\s*"  # any more whitespace before the end of the code markup
    r"(?P=delim)",  # match the exact same delimiter from the start again
    re.DOTALL | re.IGNORECASE,  # "." also matches newlines, case insensitive
)
