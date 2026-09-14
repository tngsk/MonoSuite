import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS: label: "text", id: "text", placeholder: "text", size: "small|medium|large"
    PATTERN = r"@\[textfield(?:-input)?(?!\-)(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)
        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            label, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str)
            args = {**specific_args, **common_args}

            placeholder = args.get('placeholder', '')
            size = args.get('size', '')

            # Shorthand compatibility
            if label and not placeholder:
                placeholder = label.strip()

            size_attr = f' size="{self.escape_html(size)}"' if size else ""
            safe_placeholder = self.escape_html(placeholder)
            if 'id' not in args:
                args['id'] = self.get_next_id("textfield")

            label_text = args.get('label', label)
            label_attr = f' label="{self.escape_html(label_text)}"' if label_text else ""

            return f'<mono-textfield-input placeholder="{safe_placeholder}"{size_attr}{label_attr}{self.get_common_attributes(args)}></mono-textfield-input>'
        return pattern.sub(replacer, markdown_content)
