import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-poll"]

    # OPTIONS: title: "text", options: "A,B,C"
    PATTERN = r"@\[poll(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

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
            options = args.get('options', '')

            safe_title = self.escape_html(title) if title else ""
            safe_options = self.escape_html(options)
            component_id = self.get_next_id("poll")
            return f'<mono-poll id="{component_id}" title="{safe_title}" options="{safe_options}"{self.get_common_attributes(args)}></mono-poll>'
        return pattern.sub(replacer, markdown_content)
