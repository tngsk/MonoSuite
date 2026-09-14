import sys
import os
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

spec = importlib.util.spec_from_file_location("mono_compare_parser", "src/components/mono-compare/parser.py")
mono_compare_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mono_compare_parser)
Parser = mono_compare_parser.Parser

def test_compare_parser_modes():
    parser = Parser()

    # 2要素比較のテスト（自動判定で mode="2"）
    md_2 = """::: compare
### Before
従来の問題点
:::
### After
新しい改善策
:::"""
    html_2 = parser.process(md_2)
    assert '<mono-compare mode="2"' in html_2
    assert html_2.count('<div class="compare-item"') == 2
    assert "Before" in html_2
    assert "After" in html_2

    # 3要素比較のテスト（自動判定で mode="3"、等幅並列）
    md_3 = """::: compare
### 制作者視点
設計の意図
:::
### 主成果物
共通の試作品
:::
### 利用者視点
実際の使い勝手
:::"""
    html_3 = parser.process(md_3)
    assert '<mono-compare mode="3"' in html_3
    assert html_3.count('<div class="compare-item"') == 3
    assert "制作者視点" in html_3
    assert "主成果物" in html_3
    assert "利用者視点" in html_3


def test_compare_fallback_and_attributes():
    parser = Parser()

    # 明示的な mode 指定の優先および後置属性のテスト
    md = """::: compare (mode: "2"){.custom-border #compare-section}
### 左視点
:::
### 中央視点
:::
### 右視点
:::"""
    html = parser.process(md)
    assert 'mode="2"' in html
    assert 'class="custom-border"' in html
    assert 'id="compare-section"' in html
    assert html.count('<div class="compare-item"') == 3


def test_compare_gap_options():
    parser = Parser()

    # セマンティックgap指定（item）
    md_item = """::: compare gap-item
左
:::
右
:::"""
    html_item = parser.process(md_item)
    assert 'gap="item"' in html_item

    # カスタム長gap指定（16px）
    md_custom = """::: compare (gap: "16px")
1
:::
2
:::
3
:::"""
    html_custom = parser.process(md_custom)
    assert 'gap="16px"' in html_custom

    # gap未指定の場合はデフォルト挙動
    md_default = """::: compare
A
:::
B
:::"""
    html_default = parser.process(md_default)
    assert 'gap=' not in html_default
