import re

import requests

vco_cf_worker_boi: re.Pattern = re.compile(
    r"https://paste.nextcord.dev/?\?(language=python&)?(id=(?P<id>[0-9]*))?"
)

content = "https://paste.nextcord.dev/?id=164276654744022&language=python"

# print(re.search(vco_cf_worker_boi, content).groups())

r = requests.get("https://paste.nextcord.dev/api/item?key=164276654744022")
print(r)
