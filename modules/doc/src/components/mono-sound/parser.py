import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-sound"]

    # OPTIONS: url: "url", label: "text"
    PATTERN = r"@\[sound(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)
        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            label, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str)
            args = {**specific_args, **common_args}

            url, label = self.resolve_url_and_label(label, args, ['url', 'src'], 'label')

            safe_label = self.escape_html(label) if label else ""
            safe_url = self.escape_html(url)
            component_id = self.get_next_id("sound")
            return f'<mono-sound id="{component_id}" label="{safe_label}" src="{safe_url}"{self.get_common_attributes(args)}></mono-sound>'
        return pattern.sub(replacer, markdown_content)
