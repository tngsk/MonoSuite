"""Render typed blocks to escaped HTML and collect embedded assets."""
import base64, hashlib, html, mimetypes, re
from .math_render import render_math, MathError
from .links import render_link, validate_url


def render_image(image, root, assets):
    path = (root / image['source']).resolve()
    mime = mimetypes.guess_type(path.name)[0]
    if mime not in ('image/png', 'image/jpeg', 'image/webp', 'image/gif', 'image/svg+xml'):
        raise ValueError('画像はローカルの PNG/JPEG/WebP/GIF/SVG を指定してください')
    raw = path.read_bytes()
    key = hashlib.sha256(raw).hexdigest()
    assets.setdefault(key, f'data:{mime};base64,' + base64.b64encode(raw).decode())
    return f'<img alt="{html.escape(image["alt"], quote=True)}" data-asset="{key}">'


VALID_COLORS = {"yellow", "pink", "green", "cyan", "orange", "ai", "warning"}
COLOR_ALIASES = {
    "blue": "cyan",
    "sky": "cyan",
    "red": "pink",
    "normal": "yellow",
    "purple": "ai",
}


def resolve_color(raw_arg: str | None) -> str:
    """波括弧内の引数から安全に色名を解決する（未指定または不明な場合はyellow）"""
    if not raw_arg:
        return "yellow"
    arg = raw_arg.strip().strip("{}").strip()
    match = re.search(r"(?:color\s*[:=]\s*['\"]?|\.)?([a-zA-Z]+)", arg)
    if not match:
        return "yellow"
    color = match.group(1).lower()
    color = COLOR_ALIASES.get(color, color)
    return color if color in VALID_COLORS else "yellow"


def inline(text, root, assets, cache_root=None):
    pattern = (
        r'!\[(?P<img_alt>[^\]]*)\]\((?P<img_src>[^)]+)\)'
        r'|==(?!\s)(?P<marker_text>.+?)(?<!\s)==(?:\{(?P<marker_color>[a-zA-Z0-9_.:=\s"\'-]+)\})?'
        r'|\+\+(?!\s)(?P<underline_text>.+?)(?<!\s)\+\+(?:\{(?P<underline_color>[a-zA-Z0-9_.:=\s"\'-]+)\})?'
        r'|\*\*(?P<strong1>[^*]+)\*\*'
        r'|`(?P<code>[^`]+)`'
        r'|\[(?P<link_label>[^\]]+)\]\((?P<link_url>[^)]+)\)'
        r'|__(?P<strong2>[^_]+)__'
        r'|(?<!\w)_(?P<em1>[^_]+)_(?!\w)'
        r'|(?<!\*)\*(?P<em2>[^*]+)\*(?!\*)'
        r'|(?<!\\)\$(?!\$)(?P<math>[^\n$]+?)(?<!\\)\$(?!\$)'
        r'|\\(?P<dollar>\$)'
    )
    out, pos = [], 0
    for m in re.finditer(pattern, text):
        out.append(html.escape(text[pos:m.start()]))
        if m.group('img_src') is not None:
            out.append(render_image(dict(source=m.group('img_src'), alt=m.group('img_alt')), root, assets))
        elif m.group('marker_text') is not None:
            color = resolve_color(m.group('marker_color'))
            out.append(f'<mark class="mono-marker mono-marker-{color}">' + inline(m.group('marker_text'), root, assets, cache_root) + '</mark>')
        elif m.group('underline_text') is not None:
            color = resolve_color(m.group('underline_color'))
            out.append(f'<span class="mono-underline mono-underline-{color}">' + inline(m.group('underline_text'), root, assets, cache_root) + '</span>')
        elif m.group('strong1') is not None:
            out.append('<strong>' + inline(m.group('strong1'), root, assets, cache_root) + '</strong>')
        elif m.group('link_url') is not None:
            url = validate_url(m.group('link_url'))
            out.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(m.group("link_label"))}</a>')
        elif m.group('strong2') is not None:
            out.append('<strong>' + inline(m.group('strong2'), root, assets, cache_root) + '</strong>')
        elif m.group('em1') is not None or m.group('em2') is not None:
            out.append('<em>' + inline(m.group('em1') or m.group('em2'), root, assets, cache_root) + '</em>')
        elif m.group('math') is not None:
            out.append(render_math(m.group('math'), False, root, cache_root))
        elif m.group('dollar') is not None:
            out.append('$')
        else:
            out.append('<code>' + html.escape(m.group('code')) + '</code>')
        pos = m.end()
    return ''.join(out) + html.escape(text[pos:])


def render_blocks(blocks, root, assets, previews=None, cache_root=None):
    positioned = next((b for b in blocks if b['kind'] == 'images' and len(b['images']) == 1 and b.get('position') in ('left', 'right')), None)
    if positioned:
        picture = {key: value for key, value in positioned.items() if key != 'position'}
        return '<div class="media-split '+positioned['position']+'"><div class="media-copy">'+render_blocks([b for b in blocks if b is not positioned], root, assets, previews, cache_root)+'</div>'+render_blocks([picture], root, assets, previews, cache_root)+'</div>'
    output = []
    for block in blocks:
        kind = block['kind']
        if kind == 'paragraph':
            output.append('<p>' + inline(block['text'], root, assets, cache_root) + '</p>')
        elif kind == 'images':
            count = len(block['images'])
            columns = min(count, 3)
            output.append(f'<div class="image-gallery" style="--columns:{columns}">')
            output.extend('<figure>'+render_image(image, root, assets)+'</figure>' for image in block['images'])
            output.append('</div>')
        elif kind == 'local_heading':
            output.append('<h3 class="block-heading">'+inline(block['text'], root, assets, cache_root)+'</h3>')
        elif kind == 'quote':
            output.append('<blockquote class="markdown-quote">'+render_blocks(block['blocks'], root, assets, previews, cache_root)+'</blockquote>')
        elif kind == 'list':
            tag = 'ol' if block['ordered'] else 'ul'
            start = f' start="{block["start"]}"' if block['ordered'] else ''
            output.append(f'<{tag} class="markdown-list"{start}>')
            for index, item in enumerate(block['items']):
                number = '<span class="list-number" aria-hidden="true">'+str(block['start']+index)+'</span>' if block['ordered'] else ''
                output.append('<li>'+number+render_blocks(item, root, assets, previews, cache_root)+'</li>')
            output.append(f'</{tag}>')
        elif kind == 'math':
            try:
                formula = render_math(block['text'], True, root, cache_root)
            except MathError as error:
                raise ValueError(f'{block["line"]}行: {error}') from error
            output.append('<div class="math-block">'+formula+'</div>')
        elif kind == 'code':
            label, code = html.escape(block['language']), html.escape(block['text'])
            output.append('<div class="codeblock"><div class="code-tools"><span>'+label+'</span><button class="copy-code" aria-label="コードをコピー">コピー</button><span class="copy-status" role="status"></span></div><pre tabindex="0"><code>'+code+'</code></pre></div>')
        elif kind == 'link':
            output.append(render_link(block, root, assets, previews))
        elif kind == 'table':
            def row(cells, tag):
                return '<tr>' + ''.join(f'<{tag} class="align-{a}"' + (' scope="col"' if tag == 'th' else '') + '>' + inline(cell, root, assets, cache_root) + f'</{tag}>' for cell, a in zip(cells, block['align'])) + '</tr>'
            output.append('<table class="markdown-table"><thead>' + row(block['header'], 'th') + '</thead><tbody>')
            output.extend(row(cells, 'td') for cells in block['rows'])
            output.append('</tbody></table>')
        else:
            raise ValueError('Unknown block kind: ' + str(kind))
    return ''.join(output)


def render_document(document, root, previews=None, cache_root=None):
    assets, nodes = {}, []
    for source_node in document['nodes']:
        node = {key: value for key, value in source_node.items() if key != 'blocks'}
        node['html'] = render_blocks(source_node['blocks'], root, assets, previews, cache_root)
        nodes.append(node)
    return dict(nodes=nodes, edges=document['edges'], route=document['route'], assets=assets)

