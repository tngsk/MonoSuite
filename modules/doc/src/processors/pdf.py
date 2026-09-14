import logging
from pathlib import Path

class PDFProcessor:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def export_html_to_pdf(self, html_path: Path, pdf_path: Path) -> bool:
        """HTMLファイルをPDFに変換する。改ページなしの1ページのPDFを生成。"""
        try:
            from playwright.sync_api import sync_playwright, Error as PlaywrightError
        except ImportError:
            self.logger.error("❌ PDF出力には 'playwright' パッケージが必要です。'uv add playwright' と 'uv run playwright install chromium' を実行してください。")
            return False

        try:
            self.logger.info(f"PDF出力を開始します: {pdf_path}")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # HTMLをファイルURLとして読み込む
                file_url = f"file://{html_path.absolute().as_posix()}"
                page.goto(file_url, wait_until="networkidle")

                # コンポーネントが描画されるまで少し待つ（NetworkIdleだけでは不十分な場合があるため）
                page.wait_for_timeout(1000)

                # ページ全体の高さと幅を取得して1ページの長いPDFを作成
                dimensions = page.evaluate('''() => {
                    return {
                        width: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, 1024),
                        height: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1024)
                    }
                }''')

                # width/height は "px" や "mm" などの文字列が必要
                # Playwrightの .pdf() で width と height を指定すると改ページなしで1ページになる
                width = f"{dimensions['width']}px"
                height = f"{dimensions['height']}px"

                page.pdf(
                    path=pdf_path,
                    print_background=True,
                    width=width,
                    height=height,
                    page_ranges="1", # 念のため1ページのみに制限
                )

                browser.close()
                self.logger.info(f"✅ PDF出力完了: {pdf_path}")
                return True

        except PlaywrightError as e:
            if "Executable doesn't exist at" in str(e):
                self.logger.error("❌ Playwrightのブラウザバイナリが見つかりません。'uv run playwright install chromium' を実行してください。")
            else:
                self.logger.error(f"❌ PDF出力エラー (Playwright): {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ PDF出力エラー: {e}", exc_info=True)
            return False
