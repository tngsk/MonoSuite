import re

from src.processors.base_parser import BaseComponentParser


class Parser(BaseComponentParser):
    @property
    def component_name(self) -> str:
        return "mono-synth"

    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-synth"]

    # OPTIONS: url: "url", label: "text"
    def process(self, content: str) -> str:
        # Fast path
        if f"@[{self.component_name}" not in content:
            return content

        pattern = r'@\[mono-synth([^\]]*)\](?:\(([^)]*)\))?'

        def replace(match: re.Match) -> str:
            bracket_content = match.group(1)
            paren_content = match.group(2)

            # Combine all parsed arguments
            # parse_bracket_content returns (label, specific_args)
            label, args = self.parse_bracket_content(bracket_content)
            if paren_content:
                args.update(self.parse_key_value_args(paren_content))

            # Extract specific attributes
            url, label_val = self.resolve_url_and_label(label, args, ['url', 'sample'], 'label')

            # Use common attributes to get class, id, padding, etc.
            common_attrs = self.get_common_attributes(args)

            # Add specific attributes
            if url:
                common_attrs += f' sample="{url}"'

            return f'<mono-synth{common_attrs}></mono-synth>'

        return re.sub(pattern, replace, content)
