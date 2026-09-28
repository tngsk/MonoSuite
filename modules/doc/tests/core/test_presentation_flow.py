import logging
from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig


def test_presentation_profile_injects_zoom_and_brush(tmp_path):
    logger = logging.getLogger("test")
    input_file = tmp_path / "slides.md"
    output_file = tmp_path / "slides.html"
    
    input_file.write_text("""# タイトルスライド
<!-- ここはコメントです -->
本文テキスト

---

# 2枚目のスライド
次の内容
""", encoding="utf-8")
    
    config = ConversionConfig(
        input_file=input_file,
        output_file=output_file,
        css_files=None,
        profile="presentation",
        force=True
    )
    
    converter = MarkdownToHTMLConverter(config, logger)
    converter.convert()
    
    assert output_file.exists()
    html_content = output_file.read_text(encoding="utf-8")
    
    # プレゼンテーションプロファイルでズームおよびブラシが注入されていること
    assert "mono-zoom" in html_content
    assert "mono-brush" in html_content
    # 削除されたプレゼンターコンポーネントおよびスピーカーノートタグが存在しないこと
    assert "mono-presenter" not in html_content
    assert "mono-speaker-notes" not in html_content
    # HTMLコメントが出力HTMLに含まれないこと
    assert "ここはコメントです" not in html_content
    assert "<!--" not in html_content

