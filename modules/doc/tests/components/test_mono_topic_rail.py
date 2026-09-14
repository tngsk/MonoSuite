import sys
import os
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest

spec = importlib.util.spec_from_file_location("mono_topic_rail_parser", "src/components/mono-topic-rail/parser.py")
mono_topic_rail_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mono_topic_rail_parser)
Parser = mono_topic_rail_parser.Parser

pytestmark = pytest.mark.skip(reason="トピックライン機能は開発中のため除外中")


def test_topic_rail_auto_detected():
    parser = Parser()
    md = """# 講義資料
## 導入 {.topic}
講義の全体像を説明します。
## トピック1: 基礎 {.topic}
基礎理論の解説です。
"""
    result = parser.process(md)
    assert "<mono-topic-rail></mono-topic-rail>" in result


def test_topic_rail_explicit_syntax():
    parser = Parser()
    md = """@[topic-rail]

# 資料タイトル
本文内容です。
"""
    result = parser.process(md)
    assert "<mono-topic-rail></mono-topic-rail>" in result
    assert "@[topic-rail]" not in result


def test_topic_rail_not_injected_when_absent():
    parser = Parser()
    md = """# 通常の資料
## 通常の見出し
本文内容です。
"""
    result = parser.process(md)
    assert "<mono-topic-rail>" not in result


def test_topic_rail_e2e_conversion(tmp_path):
    import logging
    from src.converter import MarkdownToHTMLConverter
    from src.config import ConversionConfig

    in_file = tmp_path / "lecture.md"
    out_file = tmp_path / "lecture.html"
    in_file.write_text("# 講義資料\n## 導入 {.topic}\n導入です。\n## トピック1 {.topic}\nトピックです。", encoding="utf-8")
    cfg = ConversionConfig(input_file=in_file, output_file=out_file)
    c = MarkdownToHTMLConverter(cfg, logging.getLogger("test"))
    assert c.convert() is True
    html = out_file.read_text(encoding="utf-8")
    assert "<mono-topic-rail>" in html
    assert "template-mono-topic-rail" in html
    assert "class MonoTopicRail" in html


def test_topic_rail_e2e_normal_doc_absence(tmp_path):
    import logging
    from src.converter import MarkdownToHTMLConverter
    from src.config import ConversionConfig

    in_file = tmp_path / "normal.md"
    out_file = tmp_path / "normal.html"
    in_file.write_text("# 通常の講義資料\n## 通常の見出し\n通常の内容です。", encoding="utf-8")
    cfg = ConversionConfig(input_file=in_file, output_file=out_file)
    c = MarkdownToHTMLConverter(cfg, logging.getLogger("test"))
    assert c.convert() is True
    html = out_file.read_text(encoding="utf-8")
    assert "<mono-topic-rail>" not in html
    assert "template-mono-topic-rail" not in html

