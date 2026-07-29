from app.services.llm.parsing import parse_json_content, strip_markdown


def test_strip_json_fence():
    raw = '```json\n{"a": 1}\n```'
    assert strip_markdown(raw) == '{"a": 1}'
    assert parse_json_content(raw) == {"a": 1}


def test_strip_plain_fence():
    raw = '```\n{"b": 2}\n```'
    assert parse_json_content(raw)["b"] == 2
