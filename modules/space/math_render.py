"""Optional build-time TeX → self-contained SVG. Never requires a browser runtime."""
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from markdown_syntax import fence_open, fence_close

VERSION = 'mathjax-3.2.2-base-ams-v1'


class MathError(ValueError):
    def __init__(self, tex, message):
        self.tex = tex
        super().__init__(f'数式 {tex!r}: {message}')


def render_math(tex, display, root):
    if not tex.strip():
        raise MathError(tex, '空の数式です')
    if len(tex) > 10000:
        raise MathError(tex, '数式は10000文字以内にしてください')
    key = hashlib.sha256((VERSION + str(display) + tex).encode()).hexdigest()
    cache = Path(root) / '.spatial-cache' / 'math' / (key + '.json')
    try:
        data = json.loads(cache.read_text())
    except (OSError, ValueError):
        try:
            result = subprocess.run(['node', str(Path(__file__).parent/'tools/math-svg.cjs')],
                input=json.dumps(dict(tex=tex, display=display)), text=True, capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise MathError(tex, 'Node.jsが必要です。数式生成の初期設定はREADMEを参照してください') from error
        if result.returncode:
            message = result.stderr.strip()
            if 'Cannot find module' in message:
                message = '数式用依存がありません。spatialで npm ci --ignore-scripts を実行してください'
            raise MathError(tex, message)
        data = json.loads(result.stdout)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding='utf-8')
    svg = data['svg']
    element = ET.fromstring(svg)
    def em(value):
        match = re.fullmatch(r'(-?[\d.]+)ex', value)
        if not match:
            raise MathError(tex, '数式の寸法を取得できません')
        return float(match[1])/2
    width, height = em(element.attrib['width']), em(element.attrib['height'])
    align = re.search(r'vertical-align:\s*(-?[\d.]+ex)', element.attrib.get('style', ''))
    depth = em(align[1]) if align else 0
    source = html.escape(tex, quote=True)
    style = f'--math-width:{width}em;--math-height:{height}em;vertical-align:{depth}em'
    # Original TeX is separate from vector paths and survives copy/paste unchanged.
    return (f'<span class="math-wrap"><button class="math-copy" data-tex="{source}" '
            f'title="TeXをコピー" aria-label="数式 {source}：TeXをコピー" style="{style}">'
            f'<span aria-hidden="true">{svg}</span></button>'
            '<span class="math-status" role="status"></span>'
            f'<code class="math-source" hidden>{source}</code></span>')


def error_line(source, tex):
    fence = None
    for number, line in enumerate(source.splitlines(), 1):
        if fence:
            if fence_close(line, fence): fence = None
            continue
        opening = fence_open(line)
        if opening:
            fence = opening[1]
            continue
        for match in re.finditer(r'`+[^`]*`+|(?<!\\)\$(?!\$)([^\n$]+?)(?<!\\)\$(?!\$)', line):
            if match[1] == tex:
                return number
    return 1
