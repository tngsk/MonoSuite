import re
from src.processors.base_parser import BaseComponentParser


class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-connector"]

    def process(self, markdown_content: str) -> str:
        if "::connect" not in markdown_content:
            return markdown_content

        pattern = re.compile(
            r'^[ \t]*::connect\s+([^\s]+)\s*->\s*([^\s|{(]+)(?:\s*\|\s*([^|{(]+?))?(?:\s*\(([^)]*)\))?(?:\s*\{([^}]*)\})?[ \t]*$',
            re.MULTILINE | re.IGNORECASE,
        )

        def replacer(match: re.Match) -> str:
            from_node = match.group(1).strip()
            to_node = match.group(2).strip()
            label = (match.group(3) or "").strip()
            args_str = match.group(4) or ""
            trailing_str = match.group(5) or ""

            args = {}
            if args_str:
                args.update(self.parse_key_value_args(args_str))
            if trailing_str:
                args = self.merge_trailing_attrs(args, trailing_str)

            args["from"] = from_node
            args["to"] = to_node
            if label and "label" not in args:
                args["label"] = label

            attrs = []
            for k, v in args.items():
                if v is not None:
                    attrs.append(f'{k}="{self.escape_html(str(v))}"')

            attr_str = (" " + " ".join(attrs)) if attrs else ""
            return f"<mono-connector{attr_str}></mono-connector>"

        return pattern.sub(replacer, markdown_content)
