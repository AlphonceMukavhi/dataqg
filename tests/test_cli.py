import json

from dataqg.cli import EXIT_ISSUES, EXIT_OK, EXIT_USAGE, main

SCHEMA = {
    "columns": {
        "id": {"type": "int"},
        "age": {"type": "int", "min": 0, "max": 120},
    },
    "key": ["id"],
}


def write(tmp_path, csv_text, schema=SCHEMA):
    csv_file = tmp_path / "data.csv"
    schema_file = tmp_path / "schema.json"
    csv_file.write_text(csv_text, encoding="utf-8")
    schema_file.write_text(json.dumps(schema), encoding="utf-8")
    return str(csv_file), str(schema_file)


def test_clean_file_exits_zero(tmp_path, capsys):
    csv_file, schema_file = write(tmp_path, "id,age\n1,30\n2,41\n")
    assert main(["validate", csv_file, "--schema", schema_file]) == EXIT_OK
    assert "0 error(s)" in capsys.readouterr().out


def test_bad_file_exits_one(tmp_path, capsys):
    csv_file, schema_file = write(tmp_path, "id,age\n1,300\n1,x\n")
    assert main(["validate", csv_file, "--schema", schema_file]) == EXIT_ISSUES
    out = capsys.readouterr().out
    assert "above max" in out and "duplicate key" in out


def test_json_output_is_parseable(tmp_path, capsys):
    csv_file, schema_file = write(tmp_path, "id,age\n1,-5\n")
    main(["validate", csv_file, "--schema", schema_file, "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["errors"] == 1


def test_missing_file_exits_two(tmp_path, capsys):
    _, schema_file = write(tmp_path, "id,age\n")
    code = main(["validate", str(tmp_path / "nope.csv"), "--schema", schema_file])
    assert code == EXIT_USAGE
    assert "dataqg: error" in capsys.readouterr().err


def test_oversized_csv_field_exits_two(tmp_path, capsys):
    huge = "x" * 200_000  # larger than the csv module's default field limit
    csv_file, schema_file = write(tmp_path, f"id,age\n1,{huge}\n")
    assert main(["validate", csv_file, "--schema", schema_file]) == EXIT_USAGE
    assert "dataqg: error" in capsys.readouterr().err
