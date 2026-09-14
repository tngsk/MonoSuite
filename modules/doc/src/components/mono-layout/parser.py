import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-layout"]

    def process(self, markdown_content: str) -> str:
        LAYOUT_KEYWORDS = (
            'hbox', 'vbox', 'h-box', 'v-box', 'layout-h', 'layout-v',
            'hstack', 'vstack', 'row', 'stack'
        )
        if not any(k in markdown_content.lower() for k in LAYOUT_KEYWORDS):
            return markdown_content

        lines = markdown_content.split("\n")
        n = len(lines)
        output = []
        stack = []

        kw_pattern = "|".join(LAYOUT_KEYWORDS)
        start_re = re.compile(
            rf'^[ \t]*(:{{3,}})[ \t]*({kw_pattern})(?:\s+(.*?))?[ \t]*$',
            re.IGNORECASE
        )
        sep_re = re.compile(r'^[ \t]*:{3,}[ \t]*(?:column|item)?[ \t]*$', re.IGNORECASE)
        end_re = re.compile(
            r'^[ \t]*:{3,}[ \t]*(?:end|/(?:hbox|vbox|layout|hstack|vstack|row|stack))[ \t]*$',
            re.IGNORECASE
        )

        def render_layout(ctx):
            items = []
            for col_lines in ctx["columns"]:
                col_text = "\n".join(col_lines).strip()
                if col_text:
                    items.append(f'<div class="column" markdown="1">\n{col_text}\n</div>')
            inner = "\n".join(items)

            attr = f' type="{ctx["type"]}"'
            if 'class' in ctx['args'] and ctx['args']['class']:
                attr += f' class="{self.escape_html(ctx["args"]["class"])}"'

            args_for_common = {k: v for k, v in ctx['args'].items() if k != 'class'}
            common_attr = self.get_common_attributes(args_for_common)
            if common_attr:
                attr += common_attr

            return f'<mono-layout{attr} markdown="1">\n{inner}\n</mono-layout>'

        for i, line in enumerate(lines):
            m = start_re.match(line)
            if m:
                fence = m.group(1)
                raw_type = m.group(2).lower()
                if raw_type in ('hbox', 'h-box', 'layout-h', 'row', 'hstack'):
                    type_name = 'hbox'
                elif raw_type in ('vbox', 'v-box', 'layout-v', 'stack', 'vstack'):
                    type_name = 'vbox'
                else:
                    type_name = 'hbox'

                meta_str = (m.group(3) or "").strip()
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
                        if token.startswith('.'):
                            classes.append(token[1:])
                        else:
                            classes.append(token)

                if classes:
                    existing_cls = args.get('class', '')
                    all_cls = " ".join([c for c in [existing_cls] + classes if c]).strip()
                    if all_cls:
                        args['class'] = all_cls

                stack.append({
                    "fence": fence,
                    "type": type_name,
                    "args": args,
                    "columns": [[]]
                })
                continue

            if stack:
                is_end = bool(end_re.match(line))
                is_sep = bool(sep_re.match(line))

                if is_end or is_sep:
                    has_next_fence = False
                    if not is_end:
                        for peek_idx in range(i + 1, n):
                            peek_line = lines[peek_idx]
                            if sep_re.match(peek_line) or end_re.match(peek_line):
                                has_next_fence = True
                                break
                    if not has_next_fence or is_end or len(stack) > 1:
                        ctx = stack.pop()
                        html_block = render_layout(ctx)
                        if stack:
                            stack[-1]["columns"][-1].append(html_block)
                        else:
                            output.append(html_block)
                        continue
                    else:
                        stack[-1]["columns"].append([])
                        continue

                stack[-1]["columns"][-1].append(line)
            else:
                output.append(line)

        while stack:
            ctx = stack.pop()
            html_block = render_layout(ctx)
            if stack:
                stack[-1]["columns"][-1].append(html_block)
            else:
                output.append(html_block)

        return "\n".join(output)
