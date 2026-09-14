import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    PATTERN = r"@\[topic-rail(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?(?:\{([^}]*)\})?"
    FAST_PATH_MARKERS = ("@[topic-rail", ".topic", ".section")

    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-topic-rail"]

    def process(self, markdown_content: str) -> str:
        has_explicit = "@[topic-rail" in markdown_content
        has_topic_class = bool(re.search(r"\{[^}]*\.(?:topic|section)[^}]*\}", markdown_content))

        if not has_explicit and not has_topic_class:
            return markdown_content

        result = markdown_content
        if has_explicit:
            pattern = re.compile(self.PATTERN)
            def replacer(match: re.Match) -> str:
                return "<mono-topic-rail></mono-topic-rail>"
            result = pattern.sub(replacer, result)

        if "<mono-topic-rail>" not in result:
            result = result + "\n\n<mono-topic-rail></mono-topic-rail>"

        return result
