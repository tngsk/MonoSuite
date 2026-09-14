import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS: front_text: "text", answer: "text"
    # Pattern: @[flipcard: "Front Text"](args)
    # The first group matches the text after the colon.
    # The second group matches the arguments inside parentheses.
    PATTERN = r"@\[flipcard(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-flipcard"]

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            # Front text is passed in the main label part.
            # Handle possible quotes.
            bracket_content = match.group(1)

            args_str = match.group(2)

            front_text, specific_args = self.parse_bracket_content(bracket_content)

            common_args = self.parse_key_value_args(args_str)

            args = {**specific_args, **common_args}

            # Accept 'a', 'A', 'ans', 'answer' as keys for the back text
            back_text = ""
            for key in ['a', 'A', 'ans', 'answer']:
                if key in args:
                    back_text = args[key]
                    break

            safe_front = self.escape_html(front_text)
            safe_back = self.escape_html(back_text)

            return f'<mono-flipcard front="{safe_front}" back="{safe_back}"{self.get_common_attributes(args)}></mono-flipcard>'

        return pattern.sub(replacer, markdown_content)
