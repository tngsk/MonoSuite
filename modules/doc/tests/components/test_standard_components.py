import importlib.util
from functools import lru_cache
from pathlib import Path
import pytest


@lru_cache(maxsize=None)
def get_parser(component_name: str):
    """コンポーネント用パーサーを動的に読み込んでキャッシュする"""
    file_path = Path(__file__).resolve().parent.parent.parent / "src" / "components" / component_name / "parser.py"
    spec = importlib.util.spec_from_file_location(f"{component_name.replace('-', '_')}_parser", str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Parser


# ============================================================================
# 基本レンダリングおよびオプションなし・全オプションのテーブル駆動テスト
# ============================================================================

BASIC_COMPONENT_CASES = [
    # (component_name, markdown, expected_snippet)
    ("mono-ab-test", '@[ab-test: "A/B Title"](src-a: "a.html", src-b: "b.html")', '<mono-ab-test'),
    ("mono-ab-test", '@[ab-test]()', '<mono-ab-test'),
    ("mono-ab-test", '@[ab-test: "Label"](src-a: "test", src-b: "test", title: "test")', '<mono-ab-test'),

    ("mono-account", '@[account]()', '<mono-account'),

    ("mono-badge", '@[badge: "New!"]()', '<mono-badge>New!</mono-badge>'),
    ("mono-badge", '@[badge]()', '<mono-badge></mono-badge>'),

    ("mono-clock", '@[clock](format: "HH:mm")', '<mono-clock format="HH:mm">'),
    ("mono-clock", '@[clock]()', '<mono-clock'),
    ("mono-clock", '@[clock: "Label"](display: "test", format: "test")', '<mono-clock'),

    ("mono-countdown", '@[countdown](time: "5m", color: "blue")', '<mono-countdown time="5m" color="blue">'),
    ("mono-countdown", '@[countdown]', '<mono-countdown></mono-countdown>'),

    ("mono-dice", '@[dice]', '<mono-dice></mono-dice>'),
    ("mono-dice", '@[dice]()', '<mono-dice'),
    ("mono-dice", '@[dice: "Label"](number: "2", faces: "10")', '<mono-dice'),

    ("mono-flipcard", '@[flipcard: "Front"](a: "Back")', '<mono-flipcard front="Front" back="Back">'),
    ("mono-flipcard", '@[flipcard: "Front"]()', '<mono-flipcard front="Front" back="">'),

    ("mono-group-assignment", '@[group-assignment](groups: 3)', '<mono-group-assignment'),
    ("mono-group-assignment", '@[group-assignment]()', '<mono-group-assignment'),
    ("mono-group-assignment", '@[group-assignment: "Label"](title: "test")', '<mono-group-assignment'),

    ("mono-icon", '@[icon: "home"](size: "md")', '<mono-icon name="home" size="md"'),
    ("mono-icon", '@[icon]()', '<mono-icon'),

    ("mono-notebook", '@[notebook: "test"]()', '<mono-notebook'),
    ("mono-notebook", '@[notebook]()', '<mono-notebook'),

    ("mono-poll", '@[poll: "Question"](options: "A,B")', '<mono-poll'),
    ("mono-poll", '@[poll]()', '<mono-poll'),

    ("mono-reaction", '@[reaction: "👍"]()', '<mono-reaction'),
    ("mono-reaction", '@[reaction]()', '<mono-reaction'),

    ("mono-score", '@[score](notes: "C4/q, D4/q")', '<mono-score notes="C4/q, D4/q">'),
    ("mono-score", '@[score]()', '<mono-score'),

    ("mono-session-join", '@[session-join: "Room 1"]()', '<mono-session-join'),
    ("mono-session-join", '@[session-join]()', '<mono-session-join'),

    ("mono-sound", '@[sound](src: "test.mp3")', 'src="test.mp3"'),
    ("mono-sound", '@[sound]()', '<mono-sound'),

    ("mono-synth", '@[mono-synth]()', '<mono-synth></mono-synth>'),

    ("mono-textfield-input", '@[textfield: "Name"]()', '<mono-textfield-input'),
    ("mono-textfield-input", '@[textfield-input]()', '<mono-textfield-input'),

    ("mono-theme", 'Some text @[theme: dark]() more text', '<mono-theme theme="dark"'),
    ("mono-theme", '@[theme: "Label"](theme_name: "test", show_ui: "test", config: "test", font_size: "16px")', '<mono-theme'),
]


@pytest.mark.parametrize("component_name,markdown,expected_snippet", BASIC_COMPONENT_CASES)
def test_standard_component_basic_rendering(component_name, markdown, expected_snippet):
    parser = get_parser(component_name)()
    result = parser.process(markdown)
    assert expected_snippet in result


# ============================================================================
# コンポーネント別の詳細機能テスト
# ============================================================================

def test_badge_variants_and_attributes():
    parser = get_parser("mono-badge")()
    assert '<mono-badge color="primary">Update</mono-badge>' in parser.process('@[badge: "Update"](color: "primary")')
    assert '<mono-badge color="secondary" soft="">Soft</mono-badge>' in parser.process('@[badge: "Soft"](color: "secondary", soft: "true")')
    assert '<mono-badge color="accent" outline="">Outline</mono-badge>' in parser.process('@[badge: "Outline"](color: "accent", outline: "true")')
    assert '<mono-badge class="custom-class" id="badge-1">Important</mono-badge>' in parser.process('@[badge: "Important"]{.custom-class #badge-1}')


def test_countdown_formats_and_multiple():
    parser = get_parser("mono-countdown")()
    assert '<mono-countdown time="30s"></mono-countdown>' in parser.process('@[countdown](time: "30s")')
    assert '<mono-countdown time="1h" color="red"></mono-countdown>' in parser.process('@[countdown]( time: "1h",  color :  "red" )')
    assert '<mono-countdown time="2026-12-31T23:59:59"></mono-countdown>' in parser.process('@[countdown](time: "2026-12-31T23:59:59")')
    multi = parser.process('@[countdown](time: "1m") and @[countdown](time: "2m", color: "green")')
    assert '<mono-countdown time="1m"></mono-countdown>' in multi
    assert '<mono-countdown time="2m" color="green"></mono-countdown>' in multi


def test_dice_parameters_and_block_tags():
    parser = get_parser("mono-dice")()
    assert parser.process('@[dice](faces: 12)') == '<mono-dice faces="12"></mono-dice>'
    assert parser.process('@[dice](number: 5)') == '<mono-dice faces="5"></mono-dice>'
    assert parser.process('@[dice](number: 3, faces: 20)') == '<mono-dice faces="3"></mono-dice>'
    assert "mono-dice" in parser.block_level_tags


def test_flipcard_keys_and_escaping():
    parser = get_parser("mono-flipcard")()
    for key in ["A", "ans", "answer"]:
        assert '<mono-flipcard front="Front" back="Back"></mono-flipcard>' in parser.process(f'@[flipcard: "Front"]({key}: "Back")')
    assert '<mono-flipcard front="Front text" back="Back text"></mono-flipcard>' in parser.process(
        "@[flipcard: 'Front text'](a: 'Back text')"
    )


def test_score_clef_time_and_voices():
    parser = get_parser("mono-score")()
    assert '<mono-score notes="C4/q" clef="bass" time="3/4"></mono-score>' in parser.process(
        '@[score](notes: "C4/q", clef: "bass", time: "3/4")'
    )
    assert '<mono-score notes="C4/q, E4/q" clef="treble"></mono-score>' in parser.process(
        '@[score: "C4/q, E4/q"](clef: treble)'
    )
    voices_result = parser.process('@[score](voices: \'["C#5/q, B4", "C#4/h"]\', clef: "treble")')
    assert 'voices="[&quot;C#5/q, B4&quot;, &quot;C#4/h&quot;]"' in voices_result
    assert 'clef="treble"' in voices_result


def test_icon_variations():
    parser = get_parser("mono-icon")()
    cases = [
        ("@[icon: search]", '<mono-icon name="search"></mono-icon>'),
        ("@[icon: search]()", '<mono-icon name="search"></mono-icon>'),
        ("@[icon: search](size: 24px)", '<mono-icon name="search" size="24px"></mono-icon>'),
        ("@[icon: search](size: 24px, color: red)", '<mono-icon name="search" size="24px" color="red"></mono-icon>'),
        ('@[icon: "quotes" test]', '<mono-icon name="&quot;quotes&quot; test"></mono-icon>'),
        ("@[icon: 'search with space']", '<mono-icon name="search with space"></mono-icon>'),
    ]
    for md, expected in cases:
        assert expected in parser.process(md)


def test_synth_parameters_and_fast_path():
    parser = get_parser("mono-synth")()
    res = parser.process('@[mono-synth](sample: "asset-mysample.wav", class: "my-synth", padding: "10px")')
    assert 'sample="asset-mysample.wav"' in res
    assert 'class="my-synth"' in res
    assert 'padding="10px"' in res
    # ファストパス（引数なし）
    plain = "Some text without synth"
    assert parser.process(plain) == plain


def test_theme_ui_and_font_size():
    parser = get_parser("mono-theme")()
    res_ui = parser.process('@[theme: corporate](show_ui: true)')
    assert '<mono-theme theme="corporate" show-ui="true"' in res_ui
    res_font = parser.process('@[theme: light](show_ui: "true", font_size: "20px")')
    assert 'font-size="20px"' in res_font
