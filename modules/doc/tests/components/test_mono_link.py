import sys
import os
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

spec = importlib.util.spec_from_file_location("mono_link_parser", "src/components/mono-link/parser.py")
mono_link_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mono_link_parser)
Parser = mono_link_parser.Parser

def test_link_parser():
    parser = Parser()
    result = parser.process("::link https://example.com")
    assert '<mono-link url="https://example.com"' in result

    # Test card style defaults
    assert 'card-style="full"' in result


def test_mono_link_no_options():
    parser = Parser()
    markdown = '::link https://example.com'
    html = parser.process(markdown)
    assert isinstance(html, str)
    assert '<mono-link' in html

def test_mono_link_all_options():
    parser = Parser()
    markdown = '::link https://example.com square\n::link-title Label'
    html = parser.process(markdown)
    assert isinstance(html, str)
    assert 'title="Label"' in html
    assert 'card-style="square"' in html

def test_mono_link_label_priority_over_ogp():
    parser = Parser()
    from unittest.mock import patch
    with patch.object(parser, 'fetch_og_data', return_value={"title": "OG Title", "desc": "OG Desc", "image": ""}):
        # When manual override title is provided
        markdown = '::link https://example.com\n::link-title My Custom Title'
        html = parser.process(markdown)
        assert 'title="My Custom Title"' in html

        # When no manual override is provided
        markdown_no_label = '::link https://example.com'
        html_no_label = parser.process(markdown_no_label)
        assert 'title="OG Title"' in html_no_label

def test_mono_link_manual_overrides():
    parser = Parser()
    markdown = '::link https://example.com\n::link-title Site\n::link-description Custom Desc\n::link-image custom.png'
    html = parser.process(markdown)
    assert 'title="Site"' in html
    assert 'desc="Custom Desc"' in html
    assert 'image="custom.png"' in html


def test_ogp_parser_and_cache(tmp_path, monkeypatch):
    parser = Parser()
    parser._memory_cache.clear()
    monkeypatch.setattr(parser, "_get_cache_dir", lambda: tmp_path)

    sample_html = (
        '<!doctype html><html><head>'
        '<meta content="サンプルサイト" property="og:title">'
        '<meta content="説明文です" property="og:description">'
        '<meta property="og:image" content="/assets/cover.png">'
        '</head><body></body></html>'
    ).encode("utf-8")

    call_count = 0
    def mock_download(url, limit, timeout=8):
        nonlocal call_count
        call_count += 1
        if url == "https://example.org/page":
            return sample_html, "text/html", "utf-8", "https://example.org/page"
        if url == "https://example.org/assets/cover.png":
            return b"fake_png_data", "image/png", "utf-8", "https://example.org/assets/cover.png"
        raise ValueError(f"Unknown url: {url}")

    monkeypatch.setattr(parser, "download_resource", mock_download)

    # 1回目の取得：パースとキャッシュ生成の検証
    data1 = parser.fetch_og_data("https://example.org/page")
    assert data1["title"] == "サンプルサイト"
    assert data1["desc"] == "説明文です"
    assert data1["image"].startswith("data:image/png;base64,")
    assert call_count == 2

    # 2回目の取得：キャッシュヒットによりダウンロードがバイパスされることの検証
    data2 = parser.fetch_og_data("https://example.org/page")
    assert data2 == data1
    assert call_count == 2


def test_ogp_security_and_fallback(monkeypatch):
    parser = Parser()
    parser._memory_cache.clear()

    # サイズ上限超過エラーをシミュレート
    def mock_oversize(url, limit, timeout=8):
        raise ValueError("プレビュー取得サイズが上限を超過しました")

    monkeypatch.setattr(parser, "download_resource", mock_oversize)
    data = parser.fetch_og_data("https://example.org/huge")
    assert data == {"title": "", "desc": "", "image": ""}

    # クラッシュせずにパーサーが安全に完了すること
    result = parser.process('::link https://example.org/huge\n::link-title Huge')
    assert 'title="Huge"' in result
    assert '<mono-link' in result


def test_ogp_cache_ttl_and_expiration(tmp_path, monkeypatch):
    import json
    import hashlib
    import time

    parser = Parser()
    parser._memory_cache.clear()
    monkeypatch.setattr(parser, "_get_cache_dir", lambda: tmp_path)

    # 1. 期限切れキャッシュファイルを直接生成
    url = "https://example.org/ttl-test"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_file = tmp_path / f"{url_hash}.json"

    old_time = time.time() - (8 * 86400)  # 8日前（7日のTTLを超過）
    cache_file.write_text(json.dumps({
        "title": "Old Title",
        "desc": "Old Desc",
        "image": "",
        "cached_at": old_time
    }), encoding="utf-8")

    call_count = 0
    def mock_download(u, limit, timeout=8):
        nonlocal call_count
        call_count += 1
        new_html = '<html><head><title>New Title</title></head></html>'.encode("utf-8")
        return new_html, "text/html", "utf-8", u

    monkeypatch.setattr(parser, "download_resource", mock_download)

    # 取得実行：期限切れのため再ダウンロードされること
    data = parser.fetch_og_data(url)
    assert call_count == 1
    assert data["title"] == "New Title"
    assert data["cached_at"] > old_time


def test_ogp_cache_ttl_stale_fallback_on_network_error(tmp_path, monkeypatch):
    import json
    import hashlib
    import time

    parser = Parser()
    parser._memory_cache.clear()
    monkeypatch.setattr(parser, "_get_cache_dir", lambda: tmp_path)

    url = "https://example.org/offline-test"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    cache_file = tmp_path / f"{url_hash}.json"

    old_time = time.time() - (10 * 86400)
    cache_file.write_text(json.dumps({
        "title": "Stale Cached Title",
        "desc": "Stale Desc",
        "image": "",
        "cached_at": old_time
    }), encoding="utf-8")

    # ネットワーク接続エラーをシミュレート
    def mock_network_error(u, limit, timeout=8):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(parser, "download_resource", mock_network_error)

    # 期限切れだがネットワーク障害のため、既存の古いキャッシュが安全に返却されること
    data = parser.fetch_og_data(url)
    assert data["title"] == "Stale Cached Title"
    assert data["desc"] == "Stale Desc"


def test_mono_link_placeholder_template_and_style():
    from pathlib import Path
    template_path = Path("src/components/mono-link/template.html")
    style_path = Path("src/components/mono-link/style.css")

    template_content = template_path.read_text(encoding="utf-8")
    style_content = style_path.read_text(encoding="utf-8")

    assert "mono-link-placeholder-icon" in template_content
    assert "<svg" in template_content
    assert ".mono-link-placeholder-icon" in style_content
    assert "display: flex;" in style_content


def test_mono_link_base64_with_plus_and_equals(monkeypatch):
    """Base64データ内に++や==が含まれる場合でもMarkdownプロセッサで属性が破壊されないことをテスト"""
    from src.processors.markdown import MarkdownProcessor
    from src.handlers.file import FileHandler
    import logging

    parser = Parser()
    monkeypatch.setattr(
        parser,
        "fetch_og_data",
        lambda u: {
            "title": "Nginx Test",
            "desc": "Test Desc",
            "image": "data:image/png;base64,iVBORw0KGgoAAA++fake++data==end=="
        }
    )

    logger = logging.getLogger("test")
    file_handler = FileHandler(logger)
    proc = MarkdownProcessor(logger, file_handler)
    proc.parsers = [p if p.__class__.__name__ != "Parser" else parser for p in proc.parsers]

    markdown_input = """# Link Test
これは ==ハイライト== と ++アンダーライン++ です。
::link https://www.nginx.com/
"""
    html = proc.convert_markdown_to_html(markdown_input)
    assert 'image="data:image/png;base64,iVBORw0KGgoAAA++fake++data==end=="' in html
    assert '<mark class="mono-marker mono-marker-yellow">ハイライト</mark>' in html
    assert '<span class="mono-underline mono-underline-yellow">アンダーライン</span>' in html
    assert "mono-underline" not in html.split("<mono-link")[1]
