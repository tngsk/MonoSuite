import logging
import subprocess
import sys
import uuid
from pathlib import Path

from mono_space.build import build as build_space

from .diagnostics import Diagnostics, DiagnosticsError
from .manifest import Manifest
from .preprocessor import Preprocessor
from .publisher import Publisher, PublisherError

logger = logging.getLogger("mono_suite")


class PipelineError(Exception):
    """一括ビルドパイプラインにおける処理エラー"""
    pass


class BuildPipeline:
    """単一Markdown原稿から配布セット（Space HTML、Doc HTML、Doc PDF、マニフェスト）をアトミック生成するパイプライン"""

    def __init__(
        self,
        input_path: Path,
        output_dir: Path | None = None,
        generate_pdf: bool = True,
        offline: bool = True,
    ):
        self.input_path = input_path.resolve()
        self.generate_pdf = generate_pdf
        self.offline = offline

        stem = self.input_path.stem
        if output_dir:
            self.target_dir = (output_dir / stem).resolve()
        else:
            self.target_dir = (Path.cwd() / "dist" / stem).resolve()

        self.build_id = uuid.uuid4().hex[:12]
        self.publisher = Publisher(self.target_dir, self.build_id)

    def _run_doc(self, input_md: Path, html_out: Path, pdf_out: Path | None) -> None:
        venv_mono_doc = Path(sys.executable).parent / "mono-doc"
        executable = str(venv_mono_doc) if venv_mono_doc.exists() else "mono-doc"
        cmd = [executable, str(input_md), "-o", str(html_out)]
        if pdf_out and self.generate_pdf:
            cmd.extend(["--pdf", str(pdf_out)])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            raise PipelineError(f"Doc変換失敗: {err_msg}")

    def run(self) -> Path:
        """パイプラインを実行し、公開されたターゲットディレクトリを返す"""
        print(f"Mono Suite ビルド開始: {self.input_path.name} (Build ID: {self.build_id})")

        # 1. 共通入力診断
        try:
            raw_content = Diagnostics.run_all(self.input_path)
        except DiagnosticsError as e:
            raise PipelineError(f"事前診断失敗: {e}") from e

        # 2. 前処理（明示ID補完およびレンダラー別サニタイズ）
        processed_content, headings = Preprocessor.inject_heading_ids(raw_content)
        space_content = Preprocessor.sanitize_for_space(processed_content)
        doc_content = Preprocessor.sanitize_for_doc(processed_content)

        # 3. 一時ディレクトリと一時原稿の準備
        temp_dir = self.publisher.prepare_temp_dir()
        temp_space_md = self.input_path.parent / f".tmp-space-{self.build_id}.md"
        temp_doc_md = self.input_path.parent / f".tmp-doc-{self.build_id}.md"

        try:
            temp_space_md.write_text(space_content, encoding="utf-8")
            temp_doc_md.write_text(doc_content, encoding="utf-8")

            # 4. Space HTML 生成
            space_out = temp_dir / "presentation.html"
            try:
                build_space(temp_space_md, space_out, offline=self.offline)
                print("✓ Space プレゼンテーションHTML生成完了")
            except Exception as e:
                raise PipelineError(f"Space変換失敗: {e}") from e

            # 5. Doc HTML および PDF 生成
            doc_html_out = temp_dir / "document.html"
            doc_pdf_out = temp_dir / "document.pdf" if self.generate_pdf else None
            self._run_doc(temp_doc_md, doc_html_out, doc_pdf_out)
            print("✓ Doc ドキュメントHTML生成完了")
            if self.generate_pdf:
                print("✓ Doc 配布用PDF生成完了")

            # 6. マニフェスト生成
            artifacts = {
                "presentation_html": space_out,
                "document_html": doc_html_out,
            }
            if self.generate_pdf and doc_pdf_out:
                artifacts["document_pdf"] = doc_pdf_out

            manifest_data = Manifest.create(
                build_id=self.build_id,
                input_path=self.input_path,
                raw_content=raw_content,
                headings=headings,
                artifacts=artifacts,
            )
            manifest_out = temp_dir / "build-manifest.json"
            Manifest.write_to_file(manifest_data, manifest_out)
            print("✓ build-manifest.json 生成完了")

            # 7. 検証とアトミック切り替え（公開）
            required = ["presentation.html", "document.html", "build-manifest.json"]
            if self.generate_pdf:
                required.append("document.pdf")

            self.publisher.publish(required)
            print(f"✅ 配布セット公開完了: {self.target_dir}")
            return self.target_dir

        except Exception:
            self.publisher.cleanup_temp()
            raise

        finally:
            # 一時原稿ファイルを確実に削除
            temp_space_md.unlink(missing_ok=True)
            temp_doc_md.unlink(missing_ok=True)
