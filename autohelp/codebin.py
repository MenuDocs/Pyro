import re
from typing import Dict, Callable

from autohelp.regexes import vco_cf_worker_boi


class CodeBinExtractor:
    """Fetches code from codebins for autohelp"""

    def __init__(self):
        self._mappings: Dict[str, Callable] = {
            "paste.nextcord.dev": self._extract_vco_bois
        }

        # REGEX
        self.vco_cf_worker_boi = vco_cf_worker_boi

    async def process(self, url: str):
        vco_cf_worker_boi = re.search()

    async def _extract_vco_bois(self, url: str, paste_id: str):
        pass
