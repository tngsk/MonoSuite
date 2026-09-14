"""
Section Modifier Markdown Extension
==================================
見出し直下の ::tone, ::style note, ::marker on/off ディレクティブを解釈し、
見出し装飾や付箋スタイル（カード枠）を自動適用するプリプロセッサ。
"""

import re
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


TONE_TO_MARKER_CLASS = {
    "neutral": "marker-normal",
    "primary": "marker-ai",
    "secondary": "marker-pink",
    "accent": "marker-green",
    "info": "marker-cyan",
    "success": "marker-green",
    "warning": "marker-warning",
    "error": "marker-pink",
}


class SectionModifierPreprocessor(Preprocessor):
    HEADING_RE = re.compile(r'^(?P<hashes>#{1,6})[ \t]+(?P<title>[^\n]+?)[ \t]*$')
    TONE_RE = re.compile(r'^[ \t]*::tone[ \t]+([a-z0-9_-]+)[ \t]*$', re.IGNORECASE)
    STYLE_RE = re.compile(r'^[ \t]*::style[ \t]+([a-z0-9_-]+)[ \t]*$', re.IGNORECASE)
    MARKER_RE = re.compile(r'^[ \t]*::marker[ \t]+(on|off)[ \t]*$', re.IGNORECASE)

    def run(self, lines: list[str]) -> list[str]:
        output = []
        i = 0
        n = len(lines)
        active_note_level = None

        while i < n:
            line = lines[i]
            hm = self.HEADING_RE.match(line)

            if hm:
                heading_level = len(hm.group('hashes'))
                # もしアクティブなノート枠があり、同レベル以上の見出しに達した場合は閉じる
                if active_note_level is not None and heading_level <= active_note_level:
                    output.append('</div>\n')
                    active_note_level = None

                title_part = hm.group('title')
                hashes = hm.group('hashes')

                # 直下のディレクティブを走査
                tone = None
                style = None
                marker = None
                j = i + 1

                while j < n:
                    next_line = lines[j]
                    tm = self.TONE_RE.match(next_line)
                    sm = self.STYLE_RE.match(next_line)
                    mm = self.MARKER_RE.match(next_line)

                    if tm:
                        tone = tm.group(1).lower()
                        j += 1
                    elif sm:
                        style = sm.group(1).lower()
                        j += 1
                    elif mm:
                        marker = mm.group(1).lower()
                        j += 1
                    else:
                        break

                # クラス生成
                added_classes = []
                if marker != 'off':
                    if tone:
                        marker_cls = TONE_TO_MARKER_CLASS.get(tone, f"marker-{tone}")
                        added_classes.extend(["marker", marker_cls])
                    elif marker == 'on':
                        added_classes.append("marker")

                # 見出しテキストに attr_list 形式でクラスを注入
                if added_classes:
                    # 既存の {...} があるか確認
                    if title_part.endswith('}') and '{' in title_part:
                        s_idx = title_part.rfind('{')
                        attr_content = title_part[s_idx+1:-1].strip()
                        existing_part = title_part[:s_idx].rstrip()
                        cls_str = " ".join(f".{c}" for c in added_classes)
                        title_part = f"{existing_part} {{{attr_content} {cls_str}}}"
                    else:
                        cls_str = " ".join(f".{c}" for c in added_classes)
                        title_part = f"{title_part} {{{cls_str}}}"

                # もし ::style note なら枠を開始
                if style == 'note':
                    tone_attr = f' data-tone="{tone}"' if tone else ''
                    output.append(f'<div class="mono-note-card"{tone_attr} markdown="1">\n')
                    active_note_level = heading_level

                output.append(f"{hashes} {title_part}")
                i = j
            else:
                output.append(line)
                i += 1

        if active_note_level is not None:
            output.append('\n</div>')

        return output


class SectionModifierExtension(Extension):
    def extendMarkdown(self, md):
        # notes拡張などの前、高い優先度でディレクティブを処理
        md.preprocessors.register(SectionModifierPreprocessor(md), "mono_section_modifier", 35)


def makeExtension(**kwargs):
    return SectionModifierExtension(**kwargs)
