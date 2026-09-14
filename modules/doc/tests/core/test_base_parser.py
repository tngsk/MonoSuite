import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.processors.base_parser import BaseComponentParser
import logging

def test_parse_key_value_args_colon():
    parser = BaseComponentParser()
    result = parser.parse_key_value_args('key: "value"')
    assert result == {"key": "value"}

def test_parse_key_value_args_colon_with_colon_in_value():
    parser = BaseComponentParser()
    result = parser.parse_key_value_args('url: "https://example.com"')
    assert result == {"url": "https://example.com"}

def test_parse_bracket_content():
    parser = BaseComponentParser()

    # 1. Label and args
    label, args = parser.parse_bracket_content('"My Label", id: "123", placeholder: "test"')
    assert label == "My Label"
    assert args == {"id": "123", "placeholder": "test"}

    # 2. Label without quotes and args
    label, args = parser.parse_bracket_content('My Label, id: "123"')
    assert label == "My Label"
    assert args == {"id": "123"}

    # 3. Only args
    label, args = parser.parse_bracket_content('id: "123", placeholder: "test"')
    assert label == ""
    assert args == {"id": "123", "placeholder": "test"}

    # 4. Only label
    label, args = parser.parse_bracket_content('"Only Label"')
    assert label == "Only Label"
    assert args == {}

    # 6. Empty content
    label, args = parser.parse_bracket_content('')
    assert label == ""
    assert args == {}


def test_parse_attr_list():
    parser = BaseComponentParser()

    # 1. Simple classes
    res1 = parser.parse_attr_list("{.gap-md .center}")
    assert res1 == {"class": "gap-md center"}

    # 2. Class and ID
    res2 = parser.parse_attr_list("{#main-nav .container}")
    assert res2 == {"class": "container", "id": "main-nav"}

    # 3. Kramdown style colon with key-value
    res3 = parser.parse_attr_list('{: .highlight data-role="modal"}')
    assert res3 == {"class": "highlight", "data-role": "modal"}

    # 4. In parse_key_value_args directly
    res4 = parser.parse_key_value_args("{.gap-lg .center}")
    assert res4 == {"class": "gap-lg center"}

def test_merge_trailing_attrs():
    parser = BaseComponentParser()

    # 1. Merge classes deduplicated, ID from trailing
    args = {"class": "btn primary", "id": "btn-orig", "color": "blue"}
    merged = parser.merge_trailing_attrs(args, "{.primary .large #btn-new}")
    assert merged["class"] == "btn primary large"
    assert merged["id"] == "btn-new"
    assert merged["color"] == "blue"

    # 2. Empty trailing
    assert parser.merge_trailing_attrs(args, "") == args

    # 3. Only trailing class and id
    args_empty = {}
    merged2 = parser.merge_trailing_attrs(args_empty, "{.custom #elem}")
    assert merged2 == {"class": "custom", "id": "elem"}

