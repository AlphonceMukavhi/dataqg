from dataqg.checks import Severity, check_cell, check_header, check_rows
from dataqg.schema import ColumnRule, parse_schema

AGE = ColumnRule(name="age", type="int", min=0, max=120)


def messages(issues):
    return [i.message for i in issues]


def test_valid_cell_has_no_issues():
    assert list(check_cell("35", AGE, row=1)) == []


def test_empty_non_nullable_cell_is_error():
    (issue,) = check_cell("", AGE, row=3)
    assert issue.severity is Severity.ERROR
    assert issue.row == 3


def test_empty_nullable_cell_is_ok():
    rule = ColumnRule(name="note", nullable=True)
    assert list(check_cell("", rule, row=1)) == []


def test_wrong_type_is_reported_once():
    issues = list(check_cell("abc", AGE, row=1))
    assert len(issues) == 1
    assert "not a valid int" in issues[0].message


def test_range_violations():
    assert "below min" in messages(check_cell("-1", AGE, 1))[0]
    assert "above max" in messages(check_cell("200", AGE, 1))[0]


def test_allowed_values():
    rule = ColumnRule(name="country", allowed=("ZW", "ZA"))
    assert list(check_cell("ZW", rule, 1)) == []
    assert len(list(check_cell("KE", rule, 1))) == 1


def test_header_missing_and_unexpected():
    schema = parse_schema({"columns": {"id": {"type": "int"}}})
    issues = list(check_header(["name"], schema))
    severities = {i.severity for i in issues}
    assert severities == {Severity.ERROR, Severity.WARNING}


def test_duplicate_keys_detected():
    schema = parse_schema({"columns": {"id": {"type": "int"}}, "key": ["id"]})
    rows = [{"id": "1"}, {"id": "2"}, {"id": "1"}]
    (issue,) = check_rows(rows, schema)
    assert issue.row == 3
    assert "first seen on row 1" in issue.message
