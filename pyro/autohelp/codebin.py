import re
from typing import Dict, Callable

from pyro.autohelp.regexes import vco_cf_worker_boi


class CodeBinExtractor:
    """Fetches code from codebins for autohelp"""

    def __init__(self, bot):
        self.vco_cf_worker_boi = vco_cf_worker_boi

        self._mappings: Dict[str, Callable] = {
            "paste.nextcord.dev": self._extract_vco_bois,
            "paste.disnake.dev": self._extract_vco_bois,
            "paste.vcokltfre.dev": self._extract_vco_bois,
            "paste.vcokltf.re": self._extract_vco_bois,
        }

        # REGEX
        self.vco_cf_worker_boi = vco_cf_worker_boi

        from pyro.bot import Pyro

        self.bot: Pyro = bot

    async def process(self, content: str) -> str:
        is_vco_workers = re.search(self.vco_cf_worker_boi, content)
        if is_vco_workers:
            url = is_vco_workers.group("url")
            paste_id = is_vco_workers.group("id")
            return await self._extract_vco_bois(url, paste_id)

        return ""

    async def _extract_vco_bois(self, url: str, paste_id: str) -> str:
        async with self.bot.session.get(f"https://{url}/api/item?key={paste_id}") as r:
            content = await r.text() if r.status == 200 else ""

        return content
