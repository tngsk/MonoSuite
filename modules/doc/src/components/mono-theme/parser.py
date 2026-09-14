import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-theme"]

    # OPTIONS: theme_name: "light|dark", show_ui: "true|false", config: "json", font_size: "16px"
    # Pattern to match @[theme: THEME_NAME]()
    PATTERN = r"@\[theme:\s*([^\]]+)\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)
        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)

            args_str = match.group(2)

            theme_name, specific_args = self.parse_bracket_content(bracket_content)

            common_args = self.parse_key_value_args(args_str)

            args = {**specific_args, **common_args} if args_str else {}

            show_ui = args.get('show_ui', 'false').lower() == 'true'
            config_file = args.get('config', '')
            font_size = args.get('font_size', '')

            safe_theme = self.escape_html(theme_name)
            safe_show_ui = "true" if show_ui else "false"
            safe_config = self.escape_html(config_file)
            safe_font_size = self.escape_html(font_size)

            font_size_attr = f' font-size="{safe_font_size}"' if safe_font_size else ""

            return f'<mono-theme theme="{safe_theme}" show-ui="{safe_show_ui}" config="{safe_config}"{font_size_attr}{self.get_common_attributes(args)}></mono-theme>'

        return pattern.sub(replacer, markdown_content)
