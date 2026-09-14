import re
from typing import List
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS:
    @property
    def pattern(self) -> re.Pattern:
        return re.compile(r"@\[account\]\(\)")

    @property
    def component_name(self) -> str:
        return "mono-account"

    @property
    def block_level_tags(self) -> List[str]:
        return ["mono-account"]

    def process(self, markdown_content: str) -> str:
        return self.pattern.sub(f'<{self.component_name}></{self.component_name}>', markdown_content)
