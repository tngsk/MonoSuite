import markdown
from src.extensions.heading_marker import HeadingMarkerExtension


def test_heading_marker_wrapping():
    md = markdown.Markdown(extensions=["attr_list", HeadingMarkerExtension()])
    text = "## 導入 {.marker-ai}"
    html = md.convert(text)
    assert '<h2 class="marker-ai"><span class="heading-highlight">導入</span></h2>' in html


def test_heading_marker_normal_heading_not_wrapped():
    md = markdown.Markdown(extensions=["attr_list", HeadingMarkerExtension()])
    text = "## 通常の見出し"
    html = md.convert(text)
    assert '<h2' in html
    assert "heading-highlight" not in html


def test_heading_marker_multiple_classes():
    md = markdown.Markdown(extensions=["attr_list", HeadingMarkerExtension()])
    text = "# 大見出し {.large .marker-warning}"
    html = md.convert(text)
    assert 'class="large marker-warning"' in html or 'class="marker-warning large"' in html
    assert '<span class="heading-highlight">大見出し</span>' in html


def test_heading_marker_prevents_double_wrapping():
    md = markdown.Markdown(extensions=["attr_list", HeadingMarkerExtension()])
    text = '<h2 class="marker"><span class="heading-highlight">すでにラップ済み</span></h2>'
    html = md.convert(text)
    assert html.count("heading-highlight") == 1

    # レガシーなheading-marker-textの二重ラップ防止も検証
    legacy_text = '<h2 class="marker"><span class="heading-marker-text">レガシーラップ</span></h2>'
    legacy_html = md.convert(legacy_text)
    assert "heading-highlight" not in legacy_html
    assert legacy_html.count("heading-marker-text") == 1
