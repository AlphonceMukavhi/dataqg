import pytest

from dataqg.schema import SchemaError, parse_schema


def test_parse_valid_schema():
    schema = parse_schema(
        {"columns": {"age": {"type": "int", "min": 0}}, "key": ["age"]}
    )
    assert schema.columns[0].name == "age"
    assert schema.columns[0].min == 0
    assert schema.key == ("age",)


@pytest.mark.parametrize(
    "raw",
    [
        {},
        {"columns": {}},
        {"columns": {"a": {"type": "datetime"}}},
        {"columns": {"a": {"type": "int"}}, "key": ["missing"]},
    ],
)
def test_parse_rejects_bad_schema(raw):
    with pytest.raises(SchemaError):
        parse_schema(raw)
