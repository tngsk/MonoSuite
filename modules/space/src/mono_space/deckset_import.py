"""Deckset slides to standard Mono Space sections; no theme emulation."""
import json
import re
from .markdown_syntax import fence_open, fence_close, image_line
from pathlib import Path
from .import_assets import ImportAssets


def split_slides(text):
    """Separators inside fenced or indented code remain literal."""
    slides, current, fence = [], [], None
    for number, line in enumerate(text.splitlines(), 1):
        delimiter = fence_open(line)
        if fence:
            current.append((number, line))
            if fence_close(line, fence):
                fence = None
        elif delimiter:
            fence = delimiter[1]
            current.append((number, line))
        elif re.fullmatch(r' {0,3}---\s*', line):
            slides.append(current); current = []
        else:
            current.append((number, line))
    slides.append(current)
    return slides


def import_document(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    md = output.with_suffix('.space.md')
    if source in (output, md, output.with_suffix('.conversion.json')):
        raise ValueError('出力先は入力ファイルと別にしてください')
    assets = ImportAssets(source.parent, output)
    slides = split_slides(source.read_text(encoding='utf-8'))
    result, changes, notes, settings = [], [], [], {}
    for index, slide in enumerate(slides):
        body, title, fence, indented = [], None, None, False
        for number, line in slide:
            delimiter = fence_open(line)
            if fence:
                body.append(line)
                if fence_close(line, fence):
                    fence = None
                continue
            if line.startswith(('    ', '\t')):
                if not indented:
                    body.append('````'); indented = True
                body.append(line[1:] if line.startswith('\t') else line[4:])
                continue
            if indented:
                if not line.strip():
                    body.append(''); continue
                body.append('````'); indented = False
            if delimiter:
                fence = delimiter[1]; body.append(line); continue
            setting = re.fullmatch(r'([a-z][a-z-]*):\s*(.*)', line)
            directive = re.fullmatch(r'\[\.([^:]+):\s*(.*?)\]', line)
            if (index == 0 and title is None and setting) or directive:
                match = directive or setting
                settings[f'{index+1}:{match[1]}'] = match[2]
                changes.append(dict(line=number, message='表示設定をレポートへ保存: '+match[1]))
                continue
            if line.startswith('^'):
                notes.append(dict(slide=index+1, text=line[1:].strip()))
                continue
            heading = re.fullmatch(r'#{1,6}\s+(?:\[fit\]\s*)?(.+)', line)
            if heading:
                if title is None:
                    title = heading[1]
                else:
                    body.extend(['', '#### '+heading[1], ''])
                continue
            image = re.fullmatch(r'!\[([^\]]*)\]\((.*)\)\s*', line)
            if image:
                modifiers, reference = image[1].split(), image[2]
                if re.search(r'\.(mov|mp4|mp3|m4a|wav)(?:$|\?)', reference, re.I) or 'youtu' in reference:
                    body.extend(['', f'動画・音声：{Path(reference).name}', ''])
                    changes.append(dict(line=number, message='動画・音声は未対応。参照を保持', reference=reference))
                    continue
                path = assets.image(reference)
                position = 'left' if 'left' in modifiers else 'right' if 'right' in modifiers else ''
                body.append(f'![]({path})')
                if position: body.append('::image-position '+position)
                unsupported = [m for m in modifiers if m not in ('left', 'right', 'fit', 'inline')]
                if unsupported:
                    changes.append(dict(line=number, message='画像指定は通常画像へ変換: '+' '.join(unsupported)))
                continue
            if line.startswith('-- '):
                body.append('> — '+line[3:]); continue
            if '<' in line and not line.lstrip().startswith('>'):
                changes.append(dict(line=number, message='HTMLは安全な文字列として表示'))
            body.append(line)
        if indented: body.append('````')
        result.extend([('# ' if index == 0 else '## ') + (title or f'Slide {index+1}'), '', *body, ''])
    output.parent.mkdir(parents=True, exist_ok=True)
    assets.write()
    md.write_text('\n'.join(result)+'\n', encoding='utf-8')
    output.with_suffix('.conversion.json').write_text(json.dumps(dict(importer='deckset', source=str(source), slides=len(slides), images=len(assets.files), settings=settings, notes=notes, changes=changes), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return md
