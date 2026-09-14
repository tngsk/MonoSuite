import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from pathlib import Path
import logging
from src.processors.pdf import PDFProcessor
from src.config import ConversionConfig

def test_pdf_processor_export_html_to_pdf_no_playwright(tmp_path, monkeypatch):
    logger = logging.getLogger("test")
    processor = PDFProcessor(logger)

    # playwright モジュールが存在しないかのようにモックする
    import sys
    monkeypatch.setitem(sys.modules, "playwright", None)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)

    html_file = tmp_path / "test.html"
    html_file.write_text("<html><body><h1>Test PDF</h1></body></html>")

    pdf_file = tmp_path / "test.pdf"

    # 実行
    result = processor.export_html_to_pdf(html_file, pdf_file)

    # アサーション（ImportErrorをキャッチしてFalseを返すはず）
    assert result is False

def test_config_resolve_pdf_output_file(tmp_path):
    input_file = tmp_path / "test.md"
    config = ConversionConfig(
        input_file=input_file,
        output_file=None,
        css_files=None,
        pdf_output=True
    )
    assert config.resolve_pdf_output_file() == tmp_path / "test.pdf"

    config2 = ConversionConfig(
        input_file=input_file,
        output_file=None,
        css_files=None,
        pdf_output=Path("custom.pdf")
    )
    assert config2.resolve_pdf_output_file() == Path("custom.pdf")

    config3 = ConversionConfig(
        input_file=input_file,
        output_file=None,
        css_files=None,
        pdf_output=None
    )
    assert config3.resolve_pdf_output_file() is None


def test_base_css_print_styles():
    css_path = Path(__file__).resolve().parents[2] / "src/templates/core/base.css"
    content = css_path.read_text(encoding="utf-8")
    assert "@media print" in content
    assert "background-image: none !important;" in content
    assert '"BIZ UDGothic"' in content
    assert "font-size: 16px !important;" in content
    assert "--font-display: 3.0rem !important;" in content
    assert "--font-title: 2.25rem !important;" in content
    assert "--font-subtitle: 1.7rem !important;" in content
    assert "--font-body: 1.35rem !important;" in content
    assert "--font-compact: 1.125rem !important;" in content
    assert "box-shadow: inset 0 -0.22em 0 0" in content
    assert "heading-highlight" in content
    assert "border: none !important;" in content
    assert "font-size: var(--font-compact) !important;" in content
    assert "white-space: pre !important;" in content
    assert "ui-monospace" in content
    assert "max-width: 100% !important;" in content
    assert "text-wrap: wrap !important;" in content
    assert "font-size: inherit !important;" in content
    assert ":not(pre) > code" in content


