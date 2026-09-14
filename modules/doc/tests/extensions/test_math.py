import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from markdown import markdown
from src.extensions.math import MathExtension

def test_math_inline():
    text = "Here is an inline math $x = y^2$ equation."
    html = markdown(text, extensions=[MathExtension()])
    assert '<span class="mono-math inline">' in html
    assert '<svg' in html
    assert "Here is an inline math" in html

def test_math_display():
    # Remove indentation to avoid standard markdown interpreting it as a code block
    text = """
Here is a block math:
$$
\\sum_{i=1}^n i = \\frac{n(n+1)}{2}
$$
End.
"""
    html = markdown(text, extensions=[MathExtension()])
    assert '<span class="mono-math display">' in html
    assert '<svg' in html
    assert "Here is a block math:" in html
    assert "End." in html

def test_math_display_protects_against_nl2br():
    from src.processors.markdown import MarkdownProcessor
    from src.handlers.file import FileHandler
    import logging

    logger = logging.getLogger(__name__)
    file_handler = FileHandler(logger)
    markdown_processor = MarkdownProcessor(logger, file_handler)

    text = """
$$
a
b
$$
"""
    html = markdown_processor.convert_markdown_to_html(text)
    assert '<br' not in html
    assert '<span class="mono-math display">' in html
    assert '<svg' in html
