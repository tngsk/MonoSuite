import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-countdown"]

    # OPTIONS: time: "10m|2024-12-31T23:59:59", color: "red|blue|..."
    PATTERN = r"@\[countdown(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"
    TEMPLATE = '<mono-countdown{time_attr}{color_attr}{common_attr}></mono-countdown>'

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            _, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str) if args_str else {}
            args = {**specific_args, **common_args}

            time_attr = ""
            color_attr = ""

            if 'time' in args:
                time_attr = f' time="{self.escape_html(args["time"])}"'
            if 'color' in args:
                color_attr = f' color="{self.escape_html(args["color"])}"'

            return self.TEMPLATE.format(
                time_attr=time_attr,
                color_attr=color_attr
            , common_attr=self.get_common_attributes(args))

        return pattern.sub(replacer, markdown_content)
