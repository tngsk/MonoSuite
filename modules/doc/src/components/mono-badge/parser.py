import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS: text: "text", color: "red|blue|...", soft: "true|false", outline: "true|false"
    PATTERN = r"@\[badge(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?(?:\{([^}]*)\})?"
    TEMPLATE = '<mono-badge{color_attr}{soft_attr}{outline_attr}{common_attr}>{text}</mono-badge>'

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            trailing_str = match.group(3) or ""

            text, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str)
            args = {**specific_args, **common_args}
            args = self.merge_trailing_attrs(args, trailing_str)

            if 'text' in args:
                text = args['text']

            color_attr = ""
            soft_attr = ""
            outline_attr = ""

            color = args.get('color') or args.get('type')
            if color:
                color_attr = f' color="{self.escape_html(color)}"'
            if 'soft' in args and args['soft'].lower() in ['true', '1', 'yes']:
                soft_attr = ' soft=""'
            if 'outline' in args and args['outline'].lower() in ['true', '1', 'yes']:
                outline_attr = ' outline=""'

            safe_text = self.escape_html(text) if text else ""

            return self.TEMPLATE.format(
                text=safe_text,
                color_attr=color_attr,
                soft_attr=soft_attr,
                outline_attr=outline_attr,
                common_attr=self.get_common_attributes(args)
            )

        return pattern.sub(replacer, markdown_content)
