import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-clock"]

    # OPTIONS: display: "analog|digital", format: "24h|12h"
    PATTERN = r"@\[clock(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"
    TEMPLATE = '<mono-clock{format_attr}{display_attr}{common_attr}></mono-clock>'

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            args_str = match.group(2)
            args = self.parse_key_value_args(args_str)

            format_attr = ""
            display_attr = ""

            if 'format' in args:
                format_attr = f' format="{self.escape_html(args["format"])}"'
            if 'display' in args:
                display_attr = f' display="{self.escape_html(args["display"])}"'

            return self.TEMPLATE.format(
                format_attr=format_attr,
                display_attr=display_attr
            , common_attr=self.get_common_attributes(args))

        return pattern.sub(replacer, markdown_content)
