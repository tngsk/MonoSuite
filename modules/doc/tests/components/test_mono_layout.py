import pytest
import importlib.util
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

spec = importlib.util.spec_from_file_location("mono_layout_parser", "src/components/mono-layout/parser.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Parser = module.Parser

@pytest.fixture
def parser():
    return Parser()

def test_mono_layout_hbox(parser):
    markdown = """::: hbox gap-md
Left
:::
Right
:::"""
    html = parser.process(markdown)
    assert '<mono-layout type="hbox" class="gap-md"' in html
    assert '<div class="column" markdown="1">\nLeft\n</div>' in html
    assert '<div class="column" markdown="1">\nRight\n</div>' in html

def test_mono_layout_vbox(parser):
    markdown = """::: vbox center
Top
:::
Bottom
:::"""
    html = parser.process(markdown)
    assert '<mono-layout type="vbox" class="center"' in html
    assert 'Top' in html
    assert 'Bottom' in html

def test_mono_layout_aliases(parser):
    markdown = """::: hstack
Left
:::
Right
:::"""
    html = parser.process(markdown)
    assert '<mono-layout type="hbox"' in html

    markdown_row = """::: row
A
:::"""
    html_row = parser.process(markdown_row)
    assert '<mono-layout type="hbox"' in html_row


def test_mono_layout_attr_list_syntax(parser):
    # 1. Pure attr_list curly brace syntax
    markdown1 = """::: hbox {.gap-lg .center}
Left
:::
Right
:::"""
    html1 = parser.process(markdown1)
    assert '<mono-layout type="hbox" class="gap-lg center"' in html1

    # 2. Options with trailing attr_list
    markdown2 = """::: vbox (gap: "md"){.items-center}
Top
:::"""
    html2 = parser.process(markdown2)
    assert '<mono-layout type="vbox" class="items-center"' in html2

def test_mono_layout_3x3_spacing_tokens(parser):
    """3x3 Spacing Trinity (gap-flow, gap-group, gap-item) が適切に属性反映されることをテスト"""
    for gap in ["gap-flow", "gap-group", "gap-item"]:
        md = f"""::: hbox {gap}
Col 1
:::
Col 2
:::"""
        html = parser.process(md)
        assert f'<mono-layout type="hbox" class="{gap}"' in html
