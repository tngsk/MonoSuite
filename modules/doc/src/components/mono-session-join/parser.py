import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-session-join"]

    # OPTIONS: title: "text"
    PATTERN = r"@\[session-join(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)
        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)

            args_str = match.group(2)

            title, specific_args = self.parse_bracket_content(bracket_content)

            common_args = self.parse_key_value_args(args_str)

            args = {**specific_args, **common_args}
            if 'title' in args:
                title = args['title']

            safe_title = self.escape_html(title) if title else ""
            return f'<mono-session-join title="{safe_title}"{self.get_common_attributes(args)}></mono-session-join>'
        return pattern.sub(replacer, markdown_content)
