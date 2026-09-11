"""Render typed blocks to escaped HTML and collect embedded assets."""
import base64, hashlib, html, mimetypes, re
from math_render import render_math, MathError
from links import render_link, validate_url


def render_image(image, root, assets):
    path = (root / image['source']).resolve()
    mime = mimetypes.guess_type(path.name)[0]
    if mime not in ('image/png', 'image/jpeg', 'image/webp', 'image/gif'):
        raise ValueError('画像はローカルの PNG/JPEG/WebP/GIF を指定してください')
    raw = path.read_bytes()
    key = hashlib.sha256(raw).hexdigest()
    assets.setdefault(key, f'data:{mime};base64,' + base64.b64encode(raw).decode())
    return f'<img alt="{html.escape(image["alt"], quote=True)}" data-asset="{key}">'


def inline(text, root, assets):
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|__([^_]+)__|(?<!\w)_([^_]+)_(?!\w)|(?<!\*)\*([^*]+)\*(?!\*)|(?<!\\)\$(?!\$)([^\n$]+?)(?<!\\)\$(?!\$)|\\(\$)'
    out, pos = [], 0
    for m in re.finditer(pattern, text):
        out.append(html.escape(text[pos:m.start()]))
        if m[2] is not None:
            out.append(render_image(dict(source=m[2], alt=m[1]), root, assets))
        elif m[3] is not None:
            out.append('<strong>' + inline(m[3], root, assets) + '</strong>')
        elif m[5] is not None:
            url = validate_url(m[6])
            out.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(m[5])}</a>')
        elif m[7] is not None:
            out.append('<strong>' + inline(m[7], root, assets) + '</strong>')
        elif m[8] is not None or m[9] is not None:
            out.append('<em>' + inline(m[8] or m[9], root, assets) + '</em>')
        elif m[10] is not None:
            out.append(render_math(m[10], False, root))
        elif m[11] is not None:
            out.append('$')
        else:
            out.append('<code>' + html.escape(m[4]) + '</code>')
        pos = m.end()
    return ''.join(out) + html.escape(text[pos:])


def render_blocks(blocks, root, assets, previews=None):
    positioned = next((b for b in blocks if b['kind'] == 'images' and len(b['images']) == 1 and b.get('position') in ('left', 'right')), None)
    if positioned:
        picture = {key: value for key, value in positioned.items() if key != 'position'}
        return '<div class="media-split '+positioned['position']+'"><div class="media-copy">'+render_blocks([b for b in blocks if b is not positioned], root, assets, previews)+'</div>'+render_blocks([picture], root, assets, previews)+'</div>'
    output = []
    for block in blocks:
        kind = block['kind']
        if kind == 'paragraph':
            output.append('<p>' + inline(block['text'], root, assets) + '</p>')
        elif kind == 'images':
            count = len(block['images'])
            columns = min(count, 3)
            output.append(f'<div class="image-gallery" style="--columns:{columns}">')
            output.extend('<figure>'+render_image(image, root, assets)+'</figure>' for image in block['images'])
            output.append('</div>')
        elif kind == 'local_heading':
            output.append('<h3 class="block-heading">'+inline(block['text'], root, assets)+'</h3>')
        elif kind == 'quote':
            output.append('<blockquote class="markdown-quote">'+render_blocks(block['blocks'], root, assets, previews)+'</blockquote>')
        elif kind == 'list':
            tag = 'ol' if block['ordered'] else 'ul'
            start = f' start="{block["start"]}"' if block['ordered'] else ''
            output.append(f'<{tag} class="markdown-list"{start}>')
            for index, item in enumerate(block['items']):
                number = '<span class="list-number" aria-hidden="true">'+str(block['start']+index)+'</span>' if block['ordered'] else ''
                output.append('<li>'+number+render_blocks(item, root, assets, previews)+'</li>')
            output.append(f'</{tag}>')
        elif kind == 'math':
            try:
                formula = render_math(block['text'], True, root)
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
                return '<tr>' + ''.join(f'<{tag} class="align-{a}"' + (' scope="col"' if tag == 'th' else '') + '>' + inline(cell, root, assets) + f'</{tag}>' for cell, a in zip(cells, block['align'])) + '</tr>'
            output.append('<table class="markdown-table"><thead>' + row(block['header'], 'th') + '</thead><tbody>')
            output.extend(row(cells, 'td') for cells in block['rows'])
            output.append('</tbody></table>')
        else:
            raise ValueError('Unknown block kind: ' + str(kind))
    return ''.join(output)


def render_document(document, root, previews=None):
    assets, nodes = {}, []
    for source_node in document['nodes']:
        node = {key: value for key, value in source_node.items() if key != 'blocks'}
        node['html'] = render_blocks(source_node['blocks'], root, assets, previews)
        nodes.append(node)
    return dict(nodes=nodes, edges=document['edges'], route=document['route'], assets=assets)

