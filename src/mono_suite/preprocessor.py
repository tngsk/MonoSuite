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
    def sanitize_for_space(cls, content: str) -> str:
        """Doc固有の ::: ブロック記法をSpaceパーサーがクラッシュしないようサニタイズする"""
        # ::: note 等を引用形式または段落に変換
        def start_replacer(match: re.Match) -> str:
            tag = match.group(1)
            return f"> [{tag}]"

        text = cls.DOC_CONTAINER_START.sub(start_replacer, content)
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
