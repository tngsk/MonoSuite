import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS: number: "1~6", faces: "4|6|8|10|12|20"
    PATTERN = r"@\[dice(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-dice"]

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            _, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str) if args_str else {}
            args = {**specific_args, **common_args}

            # Support both `faces` and `number`
            faces = args.get('number') or args.get('faces')

            attributes = []
            if faces:
                attributes.append(f'faces="{self.escape_html(faces)}"')

            attr_str = " " + " ".join(attributes) if attributes else ""
            return f'<mono-dice{attr_str}{self.get_common_attributes(args)}></mono-dice>'

        return pattern.sub(replacer, markdown_content)
