import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import markdown
from bs4 import BeautifulSoup

from src.constants import MARKDOWN_EXTENSIONS


def test_code_block_basic():
    text = """
```python
print("hello")
```
"""
    html = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(html, "html.parser")
    code_block = soup.find("mono-code-block")

    assert code_block is not None
    assert code_block.get("language") == "python"
    assert code_block.get("theme") is None


def test_code_block_with_theme():
    text = """
``` {.python theme="github"}
print("hello")
```
"""
    html = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(html, "html.parser")
    code_block = soup.find("mono-code-block")

    assert code_block is not None
    assert code_block.get("language") == "python"
    assert code_block.get("theme") == "github"


def test_code_block_with_theme_alternative_syntax():
    text = """
``` {.python theme="monokai"}
print("hello")
```
"""
    html = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(html, "html.parser")
    code_block = soup.find("mono-code-block")

    assert code_block is not None
    assert code_block.get("language") == "python"
    assert code_block.get("theme") == "monokai"


def test_code_block_no_language_with_theme():
    text = """
``` {theme="dark"}
print("hello")
```
"""
    html = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(html, "html.parser")
    code_block = soup.find("mono-code-block")

    assert code_block is not None
    assert code_block.get("language") == ""
    assert code_block.get("theme") == "dark"
