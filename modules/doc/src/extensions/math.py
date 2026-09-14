import html
import logging
import subprocess
from pathlib import Path
from xml.etree import ElementTree as etree

import markdown.util
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor

logger = logging.getLogger(__name__)


class MathInlineProcessor(InlineProcessor):
    def __init__(self, pattern, md, is_display=False):
        super().__init__(pattern, md)
        self.is_display = is_display
        self.renderer_script = Path(__file__).parent / "math_renderer.js"

    def _render_mathjax(self, math_content: str) -> str:
        if not math_content:
            return ""

        try:
            is_display_str = "true" if self.is_display else "false"
            cmd = ["node", str(self.renderer_script), is_display_str]
            result = subprocess.run(
                cmd, input=math_content, text=True, capture_output=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"MathJax CLI execution failed: {e.stderr}")
            return f'<span class="mathjax-error">{html.escape(math_content)}</span>'
        except FileNotFoundError:
            logger.error("Node.js not found. Please ensure Node.js is installed.")
            return f'<span class="mathjax-error">{html.escape(math_content)}</span>'
        except Exception as e:
            logger.error(f"An unexpected error occurred during MathJax rendering: {e}")
            return f'<span class="mathjax-error">{html.escape(math_content)}</span>'

    def handleMatch(self, m, data):
        el = etree.Element("span")
        el.set("class", "mono-math display" if self.is_display else "mono-math inline")
        math_content = m.group(1)

        svg_html = self._render_mathjax(math_content)

        # markdown.util.AtomicString returns the unescaped string but because it's set as `.text`
        # on an ElementTree element, it gets escaped by ElementTree when it renders.
        # Instead, we use `markdown.htmlStash` to inject raw HTML cleanly.
        placeholder = self.md.htmlStash.store(svg_html)
        el.text = markdown.util.AtomicString(placeholder)

        return el, m.start(0), m.end(0)


class MathExtension(Extension):
    def extendMarkdown(self, md):
        # We use (?s) to enable DOTALL (matching newlines) for display math
        display_math_pattern = r"(?s)\$\$(.*?)\$\$"
        md.inlinePatterns.register(
            MathInlineProcessor(display_math_pattern, md, True), "math_display", 175
        )

        # Inline math shouldn't span lines, standard pattern is fine
        inline_math_pattern = r"\$([^\$]+)\$"
        md.inlinePatterns.register(
            MathInlineProcessor(inline_math_pattern, md, False), "math_inline", 175
        )


def makeExtension(**kwargs):
    return MathExtension(**kwargs)
