import html
import logging
import re

from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor

logger = logging.getLogger("markdown_converter")


class CodeBlockPostprocessor(Postprocessor):
    def run(self, text):
        if "<pre" not in text:
            return text

        # Match <pre> tags which might contain attributes from extensions like attr_list
        pattern = re.compile(
            r"(<pre(?:\s+[^>]+)?><code(?:\s+[^>]+)?>(.*?)</code></pre>)", re.DOTALL
        )

        matches = list(pattern.finditer(text))
        if not matches:
            return text

        # Replace in text
        def replacer(match: re.Match) -> str:
            original_pre_and_code = match.group(1)
            code_content = match.group(2)

            # Escape HTML characters to ensure they display properly
            escaped_code = html.escape(html.unescape(code_content))

            language = ""
            lang_match = re.search(
                r'class="[^"]*language-([^"\s]+)[^"]*"', original_pre_and_code
            )
            if lang_match:
                language = lang_match.group(1)

            # Extract existing attributes from both <pre> and <code> tags to preserve them
            # Python-Markdown's attr_list can put attributes on either depending on the fence syntax
            pre_match = re.search(r"<pre([^>]*)>", original_pre_and_code)
            code_tag_match = re.search(r"<code([^>]*)>", original_pre_and_code)

            pre_attrs = pre_match.group(1) if pre_match else ""
            code_attrs = code_tag_match.group(1) if code_tag_match else ""

            # Combine attributes, but we'll extract the theme specifically
            combined_attrs = pre_attrs + " " + code_attrs

            # Extract theme if present in any of the tags
            theme = ""
            theme_match = re.search(r'theme="([^"]*)"', combined_attrs)
            if theme_match:
                theme = theme_match.group(1)

            # Clean up pre_attrs to remove redundant or internal attributes
            # 1. Remove theme attribute as it's passed explicitly
            pre_attrs = re.sub(r'\s*theme="[^"]*"', "", pre_attrs)
            # 2. Remove language class from pre_attrs if it was moved there by some extension
            pre_attrs = re.sub(r'\s*class="[^"]*language-[^"\s]+[^"]*"', "", pre_attrs)

            formatted_block = f'<pre><code class="language-{language}">{escaped_code}</code></pre>'

            theme_attr = f' theme="{theme}"' if theme else ""
            return f'<mono-code-block language="{language}"{theme_attr}{pre_attrs}>\n{formatted_block}\n</mono-code-block>'

        return pattern.sub(replacer, text)

class CodeBlockExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(CodeBlockPostprocessor(md), "code_block", 10)


def makeExtension(**kwargs):
    return CodeBlockExtension(**kwargs)
