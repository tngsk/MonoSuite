import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig
from src.logger import configure_logging

@pytest.fixture
def temp_markdown_file(tmp_path):
    md_file = tmp_path / "test.md"
    # Provide a local dummy image
    image_path = tmp_path / "dummy.png"
    import base64
    # transparent pixel
    image_path.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="))

    md_file.write_text("""
# Test Image Lazy Load
![placeholder](dummy.png)
    """)
    return md_file

def test_rendering_no_console_errors(temp_markdown_file, tmp_path):
    output_html_path = tmp_path / "output.html"
    config = ConversionConfig(input_file=Path(temp_markdown_file), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=True)
    converter = MarkdownToHTMLConverter(config, logger)

    converter.convert()

    assert output_html_path.exists()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Mock IntersectionObserver to immediately trigger intersection for lazy loading
        page.add_init_script("""
            window.IntersectionObserver = class IntersectionObserver {
                constructor(callback) {
                    this.callback = callback;
                }
                observe(element) {
                    this.callback([{ isIntersecting: true, target: element }]);
                }
                unobserve() {}
                disconnect() {}
            };
        """)

        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        page.goto(f"file://{output_html_path.absolute()}")

        # Wait for lazy loading to happen by waiting for the data-lazy-src attribute to be removed
        # If there are images, wait for them to finish updating
        images = page.locator("img")
        if images.count() > 0:
            for i in range(images.count()):
                page.locator(f"img >> nth={i}").wait_for(state="attached")
                page.wait_for_function(f"document.querySelectorAll('img')[{i}].getAttribute('data-lazy-src') === null")

        browser.close()

        # There should be no console errors or exceptions
        filtered_errors = [e for e in errors if "net::ERR_CONNECTION_REFUSED" not in e and "net::ERR_FAILED" not in e and "favicon.ico" not in e and "Failed to load resource" not in e and "/api/sync/stream" not in e and "CORS policy" not in e]
        assert len(filtered_errors) == 0, f"Found errors in browser console: {filtered_errors}"

def test_lazy_loaded_image_rendered(temp_markdown_file, tmp_path):
    output_html_path = tmp_path / "output.html"
    config = ConversionConfig(input_file=Path(temp_markdown_file), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=True)
    converter = MarkdownToHTMLConverter(config, logger)

    converter.convert()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Mock IntersectionObserver to immediately trigger intersection for lazy loading
        page.add_init_script("""
            window.IntersectionObserver = class IntersectionObserver {
                constructor(callback) {
                    this.callback = callback;
                }
                observe(element) {
                    this.callback([{ isIntersecting: true, target: element }]);
                }
                unobserve() {}
                disconnect() {}
            };
        """)

        page.goto(f"file://{output_html_path.absolute()}")

        # Wait for lazy loading to happen
        images = page.locator("img")
        if images.count() > 0:
            for i in range(images.count()):
                page.locator(f"img >> nth={i}").wait_for(state="attached")
                page.wait_for_function(f"document.querySelectorAll('img')[{i}].getAttribute('data-lazy-src') === null")

        images = page.locator("img").all()
        assert len(images) > 0

        for img in images:
            src = img.get_attribute("src")
            assert src is not None
            assert not src.startswith("data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="), "Image src was not replaced by lazy load script"

        browser.close()

def test_browser_vertical_margins_uniformity(tmp_path):
    """Playwright実機レンダリングで、トップレベル要素の垂直マージンが要素間で寸分狂わず均一であり、大画面で112px上限にクランプされることをテスト"""
    md_file = tmp_path / "margins.md"
    md_file.write_text("""# Heading 1
Paragraph 1

## Heading 2
Paragraph 2
""")
    output_html_path = tmp_path / "margins.html"
    config = ConversionConfig(input_file=Path(md_file), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=False)
    converter = MarkdownToHTMLConverter(config, logger)
    converter.convert()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # 1. 1440px（6vw = 86.4px）での均一性検証
        page_1440 = browser.new_page(viewport={"width": 1440, "height": 900})
        page_1440.goto(f"file://{output_html_path.absolute()}")
        margins_1440 = page_1440.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('body > *:not(script):not(style):not(template)'));
            return elements.map(el => parseFloat(window.getComputedStyle(el).marginBottom));
        }""")
        assert len(margins_1440) >= 3
        # 中間要素間でマージンが完全一致すること（末尾要素は:last-childで0）
        content_margins_1440 = margins_1440[:-1]
        assert len(set(round(m, 1) for m in content_margins_1440)) == 1
        for m in content_margins_1440:
            assert abs(m - 86.4) < 0.2, f"1440px margin {m} should be ~86.4px"
        assert margins_1440[-1] == 0.0, "Last element should have 0 bottom margin"

        # 2. 1920px（上限7rem = 112.0px）での均一性検証
        page_1920 = browser.new_page(viewport={"width": 1920, "height": 1080})
        page_1920.goto(f"file://{output_html_path.absolute()}")
        margins_1920 = page_1920.evaluate("""() => {
            const elements = Array.from(document.querySelectorAll('body > *:not(script):not(style):not(template)'));
            return elements.map(el => parseFloat(window.getComputedStyle(el).marginBottom));
        }""")
        assert len(margins_1920) >= 3
        content_margins_1920 = margins_1920[:-1]
        assert len(set(round(m, 1) for m in content_margins_1920)) == 1
        for m in content_margins_1920:
            assert abs(m - 112.0) < 0.2, f"1920px margin {m} should be ~112.0px"
        assert margins_1920[-1] == 0.0, "Last element should have 0 bottom margin"

        browser.close()

def test_browser_fluid_scaling_monotonic(tmp_path):
    """Playwright実機レンダリングで、画面幅拡大に伴いフォントサイズが単調増加し、順序秩序が保たれることをテスト"""
    md_file = tmp_path / "scaling.md"
    md_file.write_text("""# 大見出し
本文テキスト
""")
    output_html_path = tmp_path / "scaling.html"
    config = ConversionConfig(input_file=Path(md_file), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=False)
    converter = MarkdownToHTMLConverter(config, logger)
    converter.convert()

    viewports = [375, 768, 1440, 1920]
    h1_sizes = []
    p_sizes = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for width in viewports:
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(f"file://{output_html_path.absolute()}")
            h1_size = page.evaluate("() => parseFloat(window.getComputedStyle(document.querySelector('h1')).fontSize)")
            p_size = page.evaluate("() => parseFloat(window.getComputedStyle(document.querySelector('p')).fontSize)")
            h1_sizes.append(h1_size)
            p_sizes.append(p_size)
            assert h1_size > p_size, f"At {width}px, h1 ({h1_size}px) must be larger than p ({p_size}px)"

        browser.close()

    # 単調増加の検証（画面幅が広がるにつれてフォントサイズも拡大する）
    for i in range(len(viewports) - 1):
        assert h1_sizes[i] < h1_sizes[i+1], f"h1 size did not increase from {viewports[i]} to {viewports[i+1]}"
        assert p_sizes[i] < p_sizes[i+1], f"p size did not increase from {viewports[i]} to {viewports[i+1]}"


def test_browser_image_load_error_banner(tmp_path):
    """画像の読み込み失敗時にエラーバナーがDOMに挿入され、console.errorが出力されることをテスト"""
    md_file = tmp_path / "broken_image.md"
    md_file.write_text("""# Image Error Test
![Broken Image](https://example.invalid/non_existent.svg)
""")
    output_html_path = tmp_path / "broken_image.html"
    config = ConversionConfig(input_file=Path(md_file), output_file=output_html_path, css_files=[])
    logger = configure_logging(verbose=False)
    converter = MarkdownToHTMLConverter(config, logger)
    converter.convert()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"file://{output_html_path.absolute()}")
        page.wait_for_selector(".mono-image-error", timeout=5000)

        error_banner = page.locator(".mono-image-error")
        assert error_banner.is_visible()
        assert "画像読み込みエラー" in error_banner.text_content()
        assert "https://example.invalid/non_existent.svg" in error_banner.text_content()

        # console.error に Mono画像読み込みエラー が記録されていること
        assert any("[Mono] 画像の読み込みに失敗しました" in err for err in console_errors)

        browser.close()

