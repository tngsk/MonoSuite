import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-notebook"]

    # OPTIONS: title: "text", placeholder: "text", id: "text"
    PATTERN = r"@\[(?:notebook-input|notebook)(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            title, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str)
            args = {**specific_args, **common_args}

            input_id = args.get('id', '')
            placeholder = args.get('placeholder', '')
            if 'title' in args:
                title = args['title']

            safe_id = self.escape_html(input_id)
            attrs = []

            if title:
                safe_title = self.escape_html(title.strip())
                attrs.append(f'title="{safe_title}"')

            if placeholder:
                safe_placeholder = self.escape_html(placeholder.strip())
                attrs.append(f'placeholder="{safe_placeholder}"')

            attrs_str = " ".join(attrs)
            attr_prefix = f' {attrs_str}' if attrs_str else ''
            return f'<mono-notebook{attr_prefix}{self.get_common_attributes(args)}></mono-notebook>'

        return pattern.sub(replacer, markdown_content)
