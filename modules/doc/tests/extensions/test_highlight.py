import pytest
import markdown
from src.extensions.highlight import HighlightExtension, resolve_color
from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig
import logging


def test_resolve_color():
    assert resolve_color(None) == "yellow"
    assert resolve_color("") == "yellow"
    assert resolve_color("yellow") == "yellow"
    assert resolve_color("pink") == "pink"
    assert resolve_color(".pink") == "pink"
    assert resolve_color("{pink}") == "pink"
    assert resolve_color("color: pink") == "pink"
    assert resolve_color("green") == "green"
    assert resolve_color("cyan") == "cyan"
    assert resolve_color("blue") == "cyan"  # alias
    assert resolve_color("orange") == "orange"
    assert resolve_color("ai") == "ai"
    assert resolve_color("purple") == "ai"  # alias
    assert resolve_color("warning") == "warning"
    assert resolve_color("normal") == "yellow"  # alias
    assert resolve_color("unknown_color") == "yellow"  # fallback


def test_marker_inline_parsing():
    md = markdown.Markdown(extensions=[HighlightExtension()])
    
    # デフォルト色
    html = md.convert("これは ==重要== です。")
    assert '<mark class="mono-marker mono-marker-yellow">重要</mark>' in html
    
    # 色指定
    html_pink = md.convert("これは ==重要ピンク=={pink} です。")
    assert '<mark class="mono-marker mono-marker-pink">重要ピンク</mark>' in html_pink
    
    html_green = md.convert("これは ==重要グリーン=={.green} です。")
    assert '<mark class="mono-marker mono-marker-green">重要グリーン</mark>' in html_green
    
    html_cyan = md.convert("これは ==重要シアン=={cyan} です。")
    assert '<mark class="mono-marker mono-marker-cyan">重要シアン</mark>' in html_cyan
    
    html_orange = md.convert("これは ==重要オレンジ=={orange} です。")
    assert '<mark class="mono-marker mono-marker-orange">重要オレンジ</mark>' in html_orange

    html_ai = md.convert("これは ==重要AI=={ai} です。")
    assert '<mark class="mono-marker mono-marker-ai">重要AI</mark>' in html_ai

    html_warning = md.convert("これは ==重要警告=={warning} です。")
    assert '<mark class="mono-marker mono-marker-warning">重要警告</mark>' in html_warning


def test_underline_inline_parsing():
    md = markdown.Markdown(extensions=[HighlightExtension()])
    
    # デフォルト色
    html = md.convert("これは ++下線強調++ です。")
    assert '<span class="mono-underline mono-underline-yellow">下線強調</span>' in html
    
    # 各色指定
    html_pink = md.convert("これは ++下線ピンク++{pink} です。")
    assert '<span class="mono-underline mono-underline-pink">下線ピンク</span>' in html_pink
    
    html_cyan = md.convert("これは ++下線シアン++{cyan} です。")
    assert '<span class="mono-underline mono-underline-cyan">下線シアン</span>' in html_cyan


def test_nested_markdown_and_multiple():
    md = markdown.Markdown(extensions=[HighlightExtension()])
    
    text = "==**太字マーカー**== と ++*斜体アンダーライン*++{pink} の併用。"
    html = md.convert(text)
    assert '<mark class="mono-marker mono-marker-yellow"><strong>太字マーカー</strong></mark>' in html
    assert '<span class="mono-underline mono-underline-pink"><em>斜体アンダーライン</em></span>' in html


def test_converter_end_to_end(tmp_path):
    logger = logging.getLogger("test")
    input_file = tmp_path / "highlight_test.md"
    output_file = tmp_path / "highlight_test.html"
    
    input_file.write_text("""# マーカー機能テスト
    
これは ==黄色マーカー== と ==ピンクマーカー=={pink} です。
また、++水色アンダーライン++{cyan} と ++オレンジアンダーライン++{orange} も機能します。
""", encoding="utf-8")
    
    config = ConversionConfig(
        input_file=input_file,
        output_file=output_file,
        css_files=None,
        force=True
    )
    converter = MarkdownToHTMLConverter(config, logger)
    assert converter.convert() is True
    
    html = output_file.read_text(encoding="utf-8")
    assert '<mark class="mono-marker mono-marker-yellow">黄色マーカー</mark>' in html
    assert '<mark class="mono-marker mono-marker-pink">ピンクマーカー</mark>' in html
    assert '<span class="mono-underline mono-underline-cyan">水色アンダーライン</span>' in html
    assert '<span class="mono-underline mono-underline-orange">オレンジアンダーライン</span>' in html
    # CSSの定義が含まれていることを確認
    assert ".mono-marker" in html
    assert ".mono-underline" in html
    assert "--mono-marker-yellow" in html


def test_html_attributes_not_corrupted():
    """HTMLタグ属性値内の++や==がstash保護され誤置換されないことをテスト"""
    md = markdown.Markdown(extensions=[HighlightExtension()])
    raw = '<mono-link url="https://example.com" image="data:image/png;base64,abc++def++ghi==jkl=="></mono-link>'
    html = md.convert(raw)
    assert 'image="data:image/png;base64,abc++def++ghi==jkl=="' in html
    assert "mono-marker" not in html
    assert "mono-underline" not in html

