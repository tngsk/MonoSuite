from pathlib import Path
from mono_space.markdown_parser import parse_document
from mono_space.markdown_renderer import render_document, resolve_color, inline
from mono_space.build import build


def test_resolve_color_compatibility():
    """Docと共通の色解決仕様およびエイリアスが正しく機能することを検証"""
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
    assert resolve_color("sky") == "cyan"  # alias
    assert resolve_color("orange") == "orange"
    assert resolve_color("ai") == "ai"
    assert resolve_color("purple") == "ai"  # alias
    assert resolve_color("warning") == "warning"
    assert resolve_color("normal") == "yellow"  # alias
    assert resolve_color("unknown_color") == "yellow"  # fallback


def test_space_inline_marker_and_underline():
    """Spaceレンダラーが ==マーカー== および ++アンダーライン++ をHTML要素へ正しく変換することを検証"""
    assets = {}
    
    # 1. 既定色のマーカー
    html_marker_default = inline("これは ==重要テキスト== です", Path("."), assets)
    assert '<mark class="mono-marker mono-marker-yellow">重要テキスト</mark>' in html_marker_default

    # 2. 色指定マーカー
    html_marker_pink = inline("これは ==重要ピンク=={pink} です", Path("."), assets)
    assert '<mark class="mono-marker mono-marker-pink">重要ピンク</mark>' in html_marker_pink

    html_marker_cyan = inline("これは ==重要シアン=={blue} です", Path("."), assets)
    assert '<mark class="mono-marker mono-marker-cyan">重要シアン</mark>' in html_marker_cyan

    html_marker_ai = inline("これは ==AI強調=={ai} です", Path("."), assets)
    assert '<mark class="mono-marker mono-marker-ai">AI強調</mark>' in html_marker_ai

    # 3. 既定色のアンダーライン
    html_underline_default = inline("これは ++下線テキスト++ です", Path("."), assets)
    assert '<span class="mono-underline mono-underline-yellow">下線テキスト</span>' in html_underline_default

    # 4. 色指定アンダーライン
    html_underline_green = inline("これは ++下線グリーン++{green} です", Path("."), assets)
    assert '<span class="mono-underline mono-underline-green">下線グリーン</span>' in html_underline_green

    # 5. ネストされたマークダウン（太字など）の併用
    html_nested = inline("==**太字マーカー**== と ++`コード下線`++{orange}", Path("."), assets)
    assert '<mark class="mono-marker mono-marker-yellow"><strong>太字マーカー</strong></mark>' in html_nested
    assert '<span class="mono-underline mono-underline-orange"><code>コード下線</code></span>' in html_nested


def test_space_build_includes_highlight_styles(tmp_path: Path):
    """SpaceのプレゼンテーションHTMLビルド時にハイライトスタイルおよびデータが正しく組み込まれることを検証"""
    source = tmp_path / "test.md"
    source.write_text("# タイトル\n\nこれは ==重要情報=={pink} と ++下線補足++ です。\n", encoding="utf-8")
    output = tmp_path / "dist" / "presentation.html"
    
    data = build(source, output, offline=True)
    html_content = output.read_text(encoding="utf-8")
    
    # レンダリングされたノードHTMLの検証
    node_html = data["nodes"][0]["html"]
    assert '<mark class="mono-marker mono-marker-pink">重要情報</mark>' in node_html
    assert '<span class="mono-underline mono-underline-yellow">下線補足</span>' in node_html

    # 生成されたpresentation.html内のCSSおよびクラス定義の検証
    assert ".mono-marker" in html_content
    assert ".mono-underline" in html_content
    assert "--mono-highlight-yellow" in html_content
    assert "--mono-highlight-pink" in html_content
    assert "mono-marker-pink" in html_content
