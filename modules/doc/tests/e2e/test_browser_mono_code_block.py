import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig
from src.logger import configure_logging

@pytest.fixture
def code_block_markdown(tmp_path):
    md_file = tmp_path / "test_code.md"
    md_file.write_text("""
# Test Code Block

```python
def hello():
    print("Hello, world!")
```

``` {.javascript theme="dark"}
console.log("Dark theme js");
```
""")
    return md_file

def test_code_block_rendering(code_block_markdown, tmp_path):
    output_html_path = tmp_path / "output.html"
    config = ConversionConfig(input_file=Path(code_block_markdown), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=True)
    converter = MarkdownToHTMLConverter(config, logger)

    assert converter.convert() is True
    assert output_html_path.exists()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Grant clipboard-read permissions
        context = browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
        page = context.new_page()

        # Mock IntersectionObserver in case of lazy loading issues
        page.add_init_script("""
            window.IntersectionObserver = class IntersectionObserver {
                constructor(callback) {
                    this.callback = callback;
                }
                observe(element) {
                    this.callback([{ isIntersecting: true, target: element }]);
                }
                unobserve() {}
                disconnect() {}
            };
        """)

        page.goto(f"file://{output_html_path.absolute()}")

        # Check if code blocks exist
        code_blocks = page.locator("mono-code-block")
        assert code_blocks.count() == 2

        # First code block (python)
        cb1 = code_blocks.nth(0)
        assert cb1.get_attribute("language") == "python"

        # Check if code exists
        code1 = cb1.locator("code")
        class_attr = code1.get_attribute("class")
        assert "language-python" in class_attr

        # Second code block (javascript, dark theme)
        cb2 = code_blocks.nth(1)
        assert cb2.get_attribute("language") == "javascript"
        assert cb2.get_attribute("theme") == "dark"

        code2 = cb2.locator("code")
        class_attr = code2.get_attribute("class")
        assert "language-javascript" in class_attr

        # Test copy button functionality on the first code block
        # The copy button is in the shadow DOM
        copy_btn = cb1.locator("button.copy-button")

        # Click the copy button
        copy_btn.click()

        # Check clipboard content
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        assert 'def hello():' in clipboard_text
        assert 'print("Hello, world!")' in clipboard_text

        browser.close()
