import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-compare"]

    def process(self, markdown_content: str) -> str:
        if "compare" not in markdown_content:
            return markdown_content

        lines = markdown_content.split("\n")
        output = []
        i = 0
        n = len(lines)

        start_re = re.compile(r'^[ \t]*(:{3,})[ \t]*compare(?:\s+(.*?))?[ \t]*$', re.IGNORECASE)

        while i < n:
            line = lines[i]
            m = start_re.match(line)
            if not m:
                output.append(line)
                i += 1
                continue

            fence = m.group(1)
            fence_len = len(fence)
            meta_str = (m.group(2) or "").strip()

            args = {}
            classes = []
            if meta_str:
                if "{" in meta_str and "}" in meta_str:
                    s = meta_str.find("{")
                    e = meta_str.rfind("}")
                    args.update(self.parse_attr_list(meta_str[s:e+1]))
                    meta_str = (meta_str[:s] + meta_str[e+1:]).strip()
                if "(" in meta_str and ")" in meta_str:
                    s = meta_str.find("(")
                    e = meta_str.rfind(")")
                    args.update(self.parse_key_value_args(meta_str[s+1:e]))
                    meta_str = (meta_str[:s] + meta_str[e+1:]).strip()
                if "[" in meta_str and "]" in meta_str:
                    s = meta_str.find("[")
                    e = meta_str.rfind("]")
                    l, s_args = self.parse_bracket_content(meta_str[s+1:e])
                    if l:
                        classes.append(l)
                    args.update(s_args)
                    meta_str = (meta_str[:s] + meta_str[e+1:]).strip()
                for token in meta_str.split():
                    if token in ('2', '3'):
                        args['mode'] = token
                    elif token in ('item', 'group', 'flow', 'none'):
                        args['gap'] = token
                    elif token in ('gap-item', 'gap-group', 'gap-flow', 'gap-none'):
                        args['gap'] = token.replace('gap-', '')
                    elif token.startswith('.'):
                        classes.append(token[1:])
                    else:
                        classes.append(token)

            if classes:
                existing_cls = args.get('class', '')
                all_cls = " ".join([c for c in [existing_cls] + classes if c]).strip()
                if all_cls:
                    args['class'] = all_cls

            items = []
            current_item_lines = []
            i += 1

            while i < n:
                curr_line = lines[i]
                is_explicit_end = bool(re.match(rf'^[ \t]*:{fence_len,}[ \t]*(?:end|/compare)?[ \t]*$', curr_line, re.IGNORECASE))
                is_separator = bool(re.match(r'^[ \t]*:{3,}[ \t]*(?:column|item)?[ \t]*$', curr_line, re.IGNORECASE))

                if is_explicit_end or is_separator:
                    item_text = "\n".join(current_item_lines).strip()
                    if item_text:
                        items.append(item_text)
                    current_item_lines = []

                    if "end" in curr_line.lower() or "/compare" in curr_line.lower():
                        i += 1
                        break

                    has_subsequent_fence = False
                    for peek_idx in range(i + 1, n):
                        peek_line = lines[peek_idx]
                        if start_re.match(peek_line) or re.match(r'^[ \t]*:{3,}[ \t]*(?:hbox|vbox|section)', peek_line, re.IGNORECASE):
                            break
                        if re.match(r'^[ \t]*:{3,}', peek_line):
                            has_subsequent_fence = True
                            break

                    if not has_subsequent_fence:
                        i += 1
                        break
                    else:
                        i += 1
                        continue
                else:
                    current_item_lines.append(curr_line)
                    i += 1

            if current_item_lines:
                item_text = "\n".join(current_item_lines).strip()
                if item_text:
                    items.append(item_text)

            explicit_mode = args.get('mode')
            if explicit_mode in ('2', '3'):
                mode = explicit_mode
            else:
                mode = '3' if len(items) == 3 else '2'

            item_divs = []
            for item in items:
                item_divs.append(f'<div class="compare-item" markdown="1">\n{item}\n</div>')

            inner_html = "\n".join(item_divs)

            gap = args.get('gap')
            gap_attr = f' gap="{self.escape_html(gap)}"' if gap else ''

            args_for_common = {k: v for k, v in args.items() if k not in ('mode', 'gap')}
            common_attrs = self.get_common_attributes(args_for_common)

            output.append(f'<mono-compare mode="{mode}"{gap_attr}{common_attrs} markdown="1">\n{inner_html}\n</mono-compare>')

        return "\n".join(output)
