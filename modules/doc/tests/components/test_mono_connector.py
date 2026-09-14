import sys
import os
import importlib.util
import logging
from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

spec = importlib.util.spec_from_file_location("mono_connector_parser", "src/components/mono-connector/parser.py")
mono_connector_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mono_connector_parser)
Parser = mono_connector_parser.Parser


def test_connector_arrow_syntax():
    parser = Parser()
    md = '::connect #source -> #target (tone: "warning", curve: "step")'
    result = parser.process(md)
    assert '<mono-connector' in result
    assert 'from="#source"' in result
    assert 'to="#target"' in result
    assert 'tone="warning"' in result
    assert 'curve="step"' in result


def test_connector_arrow_syntax_with_pipe_label():
    parser = Parser()
    md = '::connect #box-a -> #box-b | データ転送 (dashed: "true", arrow: "both")'
    result = parser.process(md)
    assert '<mono-connector' in result
    assert 'from="#box-a"' in result
    assert 'to="#box-b"' in result
    assert 'label="データ転送"' in result
    assert 'dashed="true"' in result
    assert 'arrow="both"' in result


def test_connector_attribute_syntax():
    parser = Parser()
    md = '::connect #step-1 -> #step-2 | 次の処理へ (tone: "ai", from-anchor: "right", to-anchor: "left")'
    result = parser.process(md)
    assert '<mono-connector' in result
    assert 'label="次の処理へ"' in result
    assert 'from="#step-1"' in result
    assert 'to="#step-2"' in result
    assert 'tone="ai"' in result
    assert 'from-anchor="right"' in result
    assert 'to-anchor="left"' in result


def test_connector_e2e_conversion(tmp_path):
    in_file = tmp_path / "test.md"
    out_file = tmp_path / "test.html"
    in_file.write_text(
        "# 接続テスト\n\n"
        "<div id=\"node-1\">ノード1</div>\n\n"
        "<div id=\"node-2\">ノード2</div>\n\n"
        "::connect #node-1 -> #node-2 | 連携 (tone: \"ai\")\n",
        encoding="utf-8"
    )

    cfg = ConversionConfig(input_file=in_file, output_file=out_file)
    converter = MarkdownToHTMLConverter(cfg, logging.getLogger("test"))
    assert converter.convert() is True

    html = out_file.read_text(encoding="utf-8")
    assert "<mono-connector" in html
    assert 'from="#node-1"' in html
    assert 'to="#node-2"' in html
    assert 'label="連携"' in html
    assert "template-mono-connector" in html
    assert "MonoConnector" in html
    assert "mono-connector-layer" in html
