#!/usr/bin/env python3
"""Mono Space: Markdown → self-contained spatial presentation."""
import argparse
import json
import re
from pathlib import Path
from .math_render import MathError, error_line
from .links import Previews
from .importers import IMPORTERS
from .markdown_parser import parse_document
from .markdown_renderer import render_document


def parse(source, root=Path('.'), previews=None, cache_root=None):
    """Compatibility entry point: parse then render the existing output schema."""
    try:
        return render_document(parse_document(source), root, previews, cache_root)
    except MathError as error:
        number = error_line(source, error.tex)
        raise ValueError(f'{number}行: {error}') from error


def validate_styles(css):
    """Catch wrong-file writes before replacing a working presentation."""
    required = (':root', 'body', '#viewport', '#world', '.panel')
    if any(not re.search(re.escape(selector) + r'\s*\{', css) for selector in required):
        raise ValueError('styles.cssに基本スタイルがありません。HTML生成を中止しました')
    if '</style' in css.lower() or 'document.querySelector' in css or '"use strict"' in css:
        raise ValueError('styles.cssにCSS以外のコードが含まれています。HTML生成を中止しました')


def build(source, output, refresh=False, offline=False):
    cache_root = output.parent / '.spatial-cache'
    previews = Previews(cache_root, refresh=refresh, offline=offline)
    data = parse(source.read_text(encoding='utf-8'), source.parent, previews, cache_root)
    base = Path(__file__).parent / 'web'
    template = (base / 'engine.html').read_text(encoding='utf-8')
    css = (base / 'styles.css').read_text(encoding='utf-8')
    validate_styles(css)
    js = '\n'.join((base / name).read_text(encoding='utf-8') for name in ('core.js', 'layout.js', 'motion.js', 'input.js', 'stickies.js', 'app.js'))
    template = template.replace('__SPATIAL_CSS__', css).replace('__SPATIAL_JS__', js)
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.replace('__SPATIAL_DATA__', payload), encoding='utf-8')
    return data

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('source', type=Path)
    cli.add_argument('-o', '--output', type=Path, default=Path('dist/presentation.html'))
    cli.add_argument('--refresh-links', action='store_true', help='OGPキャッシュを更新')
    cli.add_argument('--offline', action='store_true', help='ネットワーク取得なしで生成')
    cli.add_argument('--from', dest='source_format', choices=tuple(IMPORTERS), default='space', help='入力記法（既定: space）')
    args = cli.parse_args()
    try:
        source = args.source
        source = IMPORTERS[args.source_format](source, args.output)
        result = build(source, args.output, args.refresh_links, args.offline)
    except (ValueError, OSError) as error:
        cli.exit(1, f'生成エラー: {error}\n')
    print(f'{args.output}: {len(result["nodes"])} nodes, {len(result["edges"])} connections')
