import markdown
from src.constants import MARKDOWN_EXTENSIONS

def test_section_modifier_tone():
    md_text = """## タイトル
::tone warning
本文です。
"""
    html = markdown.markdown(md_text, extensions=MARKDOWN_EXTENSIONS)
    assert 'class="heading-highlight">タイトル</span>' in html
    assert 'class="marker marker-warning"' in html

def test_section_modifier_marker_off():
    md_text = """## タイトル
::tone warning
::marker off
本文です。
"""
    html = markdown.markdown(md_text, extensions=MARKDOWN_EXTENSIONS)
    assert 'class="marker' not in html

def test_section_modifier_style_note():
    md_text = """## 重要事項
::tone warning
::style note
付箋の内容です。

## 次の項目
通常のセクションです。
"""
    html = markdown.markdown(md_text, extensions=MARKDOWN_EXTENSIONS)
    assert '<div class="mono-note-card" data-tone="warning"' in html
    assert '付箋の内容です。' in html
    assert '</div>' in html
    assert '次の項目</h2>' in html
