# dataqg

A small command-line tool that checks a CSV file against a JSON schema and fails loudly when the data is wrong. I built it so bad data is stopped before it reaches a database or a model: wrong types, values out of range, unexpected categories, missing values and duplicate keys.

It has no runtime dependencies, only the Python standard library.

## Usage

```bash
uv sync
uv run dataqg validate examples/people.csv --schema examples/schema.json
uv run dataqg validate examples/people.csv --schema examples/schema.json --format json
```

A schema describes each column and the key:

```json
{
  "columns": {
    "id": {"type": "int"},
    "age": {"type": "int", "min": 0, "max": 120},
    "country": {"type": "str", "allowed": ["ZW", "ZA", "KE"]},
    "score": {"type": "float", "nullable": true}
  },
  "key": ["id"]
}
```

Exit codes make it easy to use in scripts and CI pipelines:

| Code | Meaning |
|---|---|
| 0 | The data is clean |
| 1 | Data problems were found (each one is reported with its row and column) |
| 2 | Bad input: missing file, unreadable CSV or invalid schema |

## How it is organised

- `schema.py` loads and validates the schema itself.
- `checks.py` holds the column and row checks.
- `report.py` formats the issues as text or JSON.
- `cli.py` handles arguments, exit codes and errors.

## Tests and CI

```bash
uv run pytest -q          # unit and CLI tests
uv run ruff check .       # lint
uv run mypy src           # type checks
```

GitHub Actions runs formatting, linting, type checks and the tests on every push and pull request.

## Why I built it

I built this while teaching myself backend and data engineering. I wanted a first project that was small but complete: clear errors, tests, typing and CI.
