import re

vco_cf_worker_boi: re.Pattern = re.compile(
    r"https://paste.nextcord.dev/?\?(language=python&)?(id=(?P<id>[0-9]*))?"
)

content = "https://paste.nextcord.dev/?id=164257907872285&language=python \n\n https://paste.disnake.dev/?id=1642579086677101&language=python"

print(re.search(vco_cf_worker_boi, content).groups())
