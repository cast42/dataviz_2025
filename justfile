# Just file based on : https://github.com/hynek/hello-svc-part-2/blob/main/Justfile

# Use fish as the shell for running recipes
set shell := ["fish", "-c"]

ARGS_TEST := env("_UV_RUN_ARGS_TEST", "")

@_:
    just --list

# Run tests
[group('qa')]
test *args:
    uv run {{ ARGS_TEST }} -m pytest {{ args }}


# Run Ruff linter
[group('qa')]
check *args:
    uv run ruff check --fix {{ args }}
    
# Check types
[group('qa')]
typing *args:
    uvx ty check --python .venv {{ args }}


# Update dependencies
[group('lifecycle')]
update:
    uv sync --upgrade

# Ensure project virtualenv is up to date
[group('lifecycle')]
install:
    uv sync

# Remove temporary files
[group('lifecycle')]
clean:
    rm -rf .venv .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
    find . -type d -name "__pycache__" -exec rm -r {} +

# Recreate project virtualenv from nothing
[group('lifecycle')]
fresh: clean install
