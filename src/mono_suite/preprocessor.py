import re
from typing import NamedTuple


class HeadingInfo(NamedTuple):
    id: str
    title: str
    level: int
    is_explicit: bool


class Preprocessor:
    """Markdown原稿の見出しID自動補完およびレンダラー別構文サニタイズを行うクラス"""

    HEADING_REGEX = re.compile(r'^(#{1,6})\s+(.+?)(?:\s+\{#([\w-]+)\})?\s*$', re.MULTILINE)
    DOC_CONTAINER_START = re.compile(r'^[ \t]*:::[ \t]*(\w+)(?:[ \t]+(.*?))?[ \t]*$', re.MULTILINE)
    DOC_CONTAINER_END = re.compile(r'^[ \t]*:::[ \t]*$', re.MULTILINE)
    SPACE_DIRECTIVE_PATTERN = re.compile(r'^[ \t]*::(layout|tone|focus|marker|style)\s+(\w+)[ \t]*$', re.MULTILINE)

    @classmethod
    def inject_heading_ids(cls, content: str) -> tuple[str, list[HeadingInfo]]:
        """明示IDのない見出しに自動ID（sec-1, sec-2...）を付与し、見出し一覧を抽出する"""
        headings: list[HeadingInfo] = []
        counter = 0

        def replacer(match: re.Match) -> str:
            nonlocal counter
            counter += 1
            hashes = match.group(1)
            title = match.group(2).strip()
            explicit_id = match.group(3)

            if explicit_id:
                h_id = explicit_id
                is_explicit = True
            else:
                h_id = f"sec-{counter}"
                is_explicit = False

            headings.append(HeadingInfo(id=h_id, title=title, level=len(hashes), is_explicit=is_explicit))
            return f"{hashes} {title} {{#{h_id}}}"

        processed = cls.HEADING_REGEX.sub(replacer, content)
        return processed, headings

    @classmethod
    def merge_preamble_for_space(cls, content: str) -> str:
        """最初の見出しより前に存在するテキスト（キャッチコピー等）を最初の見出し本文へ合流させる"""
        lines = content.splitlines(keepends=True)
        preamble_lines: list[str] = []
        heading_index = -1

        for i, raw_line in enumerate(lines):
            line = raw_line.rstrip("\r\n")
            if cls.HEADING_REGEX.match(line):
                heading_index = i
                break
            preamble_lines.append(raw_line)

        # 見出しが見つからない、またはプリアンブルが実質空（空白行のみ）の場合はそのまま返す
        if heading_index == -1 or not any(p.strip() for p in preamble_lines):
            return content

        # 最初の見出しの直後に続くSpaceディレクティブ行（::layout 等）を探す
        insert_index = heading_index + 1
        while insert_index < len(lines):
            stripped = lines[insert_index].strip()
            if stripped.startswith("::") and not stripped.startswith(":::"):
                insert_index += 1
            else:
                break

        # プリアンブルの実質内容（前後の空行をトリミング）
        preamble_text = "".join(preamble_lines).strip()
        if not preamble_text:
            return content

        # 見出し（＋ディレクティブ）の後にプリアンブルを挿入
        result_lines = []
        result_lines.extend(lines[heading_index:insert_index])
        result_lines.append(f"\n{preamble_text}\n\n")
        result_lines.extend(lines[insert_index:])

        return "".join(result_lines)

    @classmethod
    def sanitize_for_space(cls, content: str) -> str:
        """Doc固有の ::: ブロック記法をサニタイズし、見出し前のプリアンブルを先頭見出しに合流させる"""
        # 1. 最初の見出し前のプリアンブルを先頭見出し本文へ合流
        merged = cls.merge_preamble_for_space(content)

        # 2. ::: note 等を引用形式または段落に変換
        def start_replacer(match: re.Match) -> str:
            tag = match.group(1)
            return f"> [{tag}]"

        text = cls.DOC_CONTAINER_START.sub(start_replacer, merged)
        text = cls.DOC_CONTAINER_END.sub("", text)
        return text

    @classmethod
    def sanitize_for_doc(cls, content: str) -> str:
        """Space固有の ::layout や ::focus ディレクティブをDoc本文から隠蔽（HTMLコメント化）する"""
        # ::connect はDoc側でも mono-connector パーサーが処理できるため残す
        def directive_replacer(match: re.Match) -> str:
            directive_line = match.group(0).strip()
            return f"<!-- {directive_line} -->"

        return cls.SPACE_DIRECTIVE_PATTERN.sub(directive_replacer, content)
