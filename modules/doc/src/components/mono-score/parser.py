import re
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    # OPTIONS: notes: "C4 D4 E4", clef: "treble|bass", time: "4/4|3/4", voices: '["C4 D4", "E4 F4"]'
    PATTERN = r"@\[score(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?"
    TEMPLATE = '<mono-score{notes_attr}{voices_attr}{clef_attr}{time_signature_attr}{common_attr}></mono-score>'

    def process(self, markdown_content: str) -> str:
        pattern = re.compile(self.PATTERN)

        def replacer(match: re.Match) -> str:
            bracket_content = match.group(1)
            args_str = match.group(2)
            notes, specific_args = self.parse_bracket_content(bracket_content)
            common_args = self.parse_key_value_args(args_str) if args_str else {}
            args = {**specific_args, **common_args}

            if 'notes' in args:
                notes = args['notes']

            notes_attr = f' notes="{self.escape_html(notes)}"' if notes else ""

            voices_attr = ""
            if 'voices' in args:
                voices_attr = f' voices="{self.escape_html(args["voices"])}"'

            clef_attr = ""
            if 'clef' in args:
                clef_attr = f' clef="{self.escape_html(args["clef"])}"'

            time_signature_attr = ""
            if 'time' in args:
                time_signature_attr = f' time="{self.escape_html(args["time"])}"'

            return self.TEMPLATE.format(
                notes_attr=notes_attr,
                voices_attr=voices_attr,
                clef_attr=clef_attr,
                time_signature_attr=time_signature_attr
            , common_attr=self.get_common_attributes(args))

        return pattern.sub(replacer, markdown_content)
