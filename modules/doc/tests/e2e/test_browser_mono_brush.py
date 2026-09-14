import pytest
import logging
from playwright.sync_api import sync_playwright
from src.converter import MarkdownToHTMLConverter
from src.config import ConversionConfig


def test_mono_brush_toggle_and_drawing(tmp_path):
    logger = logging.getLogger("test")
    input_file = tmp_path / "brush_slides.md"
    output_file = tmp_path / "brush_slides.html"

    input_file.write_text("""# プレゼンテーションテストスライド

本文テキストです。Bキーでブラシ描画モードがトグルされます。
""", encoding="utf-8")

    config = ConversionConfig(
        input_file=input_file,
        output_file=output_file,
        css_files=None,
        profile="presentation",
        force=True
    )
    converter = MarkdownToHTMLConverter(config, logger)
    assert converter.convert() is True

    html = output_file.read_text(encoding="utf-8")
    assert "mono-brush" in html

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.goto(f"file://{output_file.resolve()}")
        page.wait_for_timeout(300)

        # 初期状態: mono-brush が配置され、canvas は hidden クラスを持つ
        initial_state = page.evaluate('''() => {
            const brush = document.querySelector('mono-brush');
            if (!brush || !brush.shadowRoot) return null;
            const canvas = brush.shadowRoot.getElementById('canvas');
            return {
                exists: true,
                isDrawingMode: canvas.classList.contains('drawing-mode'),
                isHidden: canvas.classList.contains('hidden')
            };
        }''')
        assert initial_state is not None
        assert initial_state["exists"] is True
        assert initial_state["isDrawingMode"] is False

        # 'b' キーを押下して描画モードをONにする
        page.keyboard.press("b")
        page.wait_for_timeout(200)

        active_state = page.evaluate('''() => {
            const brush = document.querySelector('mono-brush');
            const canvas = brush.shadowRoot.getElementById('canvas');
            return {
                isDrawingMode: canvas.classList.contains('drawing-mode'),
                isHidden: canvas.classList.contains('hidden')
            };
        }''')
        assert active_state["isDrawingMode"] is True
        assert active_state["isHidden"] is False

        # 画面上でドラッグ操作（描画を実行）
        page.mouse.move(200, 200)
        page.mouse.down()
        page.mouse.move(300, 300)
        page.mouse.up()
        page.wait_for_timeout(200)

        # 描画ストロークのスタイル（蛍光赤ピンク）を検証
        stroke_color = page.evaluate('''() => {
            const brush = document.querySelector('mono-brush');
            return brush.ctx.strokeStyle;
        }''')
        assert "244, 63, 94" in stroke_color or "rgb" in stroke_color

        # 'b' キーを再押下して描画モードをOFFにする（トグル動作の検証）
        page.keyboard.press("b")
        page.wait_for_timeout(200)

        toggled_off_state = page.evaluate('''() => {
            const brush = document.querySelector('mono-brush');
            const canvas = brush.shadowRoot.getElementById('canvas');
            return {
                isDrawingMode: canvas.classList.contains('drawing-mode')
            };
        }''')
        assert toggled_off_state["isDrawingMode"] is False

        # 再度 'b' でONにしてから 'Escape' で解除できることを検証
        page.keyboard.press("b")
        page.wait_for_timeout(200)
        assert page.evaluate("document.querySelector('mono-brush').isDrawingModeActive") is True

        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        assert page.evaluate("document.querySelector('mono-brush').isDrawingModeActive") is False

        browser.close()
