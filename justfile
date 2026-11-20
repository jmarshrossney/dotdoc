# Run the full check suite: lint, typecheck, test, docs.
_:
  @just lint typecheck test docs

# Format and lint the package using ruff.
[group('check')]
lint:
  ruff format
  ruff check --fix

# Variant of `lint` that doesn't cause any changes to files (for CI).
[group('check')]
lint-check:
  ruff format --check
  ruff check

# Run static type checker.
[group('check')]
typecheck:
  pyright

# Run the test suite using pytest.
[group('test')]
test:
  pytest

# Run tests with coverage report.
[group('test')]
test-cov:
  pytest --cov=dotdoc --cov-report=term-missing --cov-fail-under=90

# Run doctest examples embedded in source docstrings.
[group('test')]
doctest:
  pytest --doctest-modules src/dotdoc

# Build the documentation using Zensical.
[group('docs')]
docs:
  zensical build

# Serve the documentation locally with live reload.
[group('docs')]
docs-serve:
  zensical serve

# Pin the uv hook and uv_build to the installed uv, update the other hooks, relock.
[group('maintain')]
bump:
  #!/usr/bin/env bash
  set -euo pipefail
  v=$(uv self version --short)
  IFS=. read -r major minor _ <<< "$v"
  floor="$major.$minor.0"
  cap="$major.$((minor + 1)).0"
  pre-commit autoupdate \
    --repo https://github.com/astral-sh/ruff-pre-commit \
    --repo https://github.com/RobertCraigie/pyright-python
  sed -i.bak -E "/astral-sh\/uv-pre-commit/,/rev:/ s/(rev:[[:space:]]*)v?[0-9.]+/\1$v/" \
    .pre-commit-config.yaml
  sed -i.bak -E "s/uv_build>=[0-9.]+,<[0-9.]+/uv_build>=$floor,<$cap/" pyproject.toml
  rm .pre-commit-config.yaml.bak pyproject.toml.bak
  grep -q "rev: $v$" .pre-commit-config.yaml \
    || { echo "uv-pre-commit rev not rewritten in .pre-commit-config.yaml" >&2; exit 1; }
  grep -q "uv_build>=$floor,<$cap" pyproject.toml \
    || { echo "uv_build requirement not rewritten in pyproject.toml" >&2; exit 1; }
  uv lock
  # A uv inside the range builds with its own backend and skips resolving
  # uv_build; forcing PEP 517 checks what other frontends and uv versions see.
  uv build --force-pep517 --wheel --out-dir "$(mktemp -d)" >/dev/null \
    || { echo "uv_build>=$floor is not installable; it may be newer than the exclude-newer cutoff" >&2; exit 1; }
  git --no-pager diff --stat

# Tag the pyproject.toml version and publish it as a GitHub release and to PyPI.
[group('release')]
release:
  #!/usr/bin/env bash
  set -euo pipefail
  v=$(uv version --short)
  [[ $v != *dev* ]] || { echo "refusing to release dev version $v" >&2; exit 1; }
  [[ $(git branch --show-current) == main ]] || { echo "not on main" >&2; exit 1; }
  git diff --quiet HEAD || { echo "uncommitted changes" >&2; exit 1; }
  git fetch --quiet origin main
  [[ $(git rev-parse HEAD) == $(git rev-parse origin/main) ]] \
    || { echo "main differs from origin/main" >&2; exit 1; }
  gh auth status >/dev/null || { echo "gh is not logged in" >&2; exit 1; }
  pre=()
  [[ ! $v =~ (a|b|rc)[0-9]+$ ]] || pre=(--prerelease)
  git tag -a "v$v" -m "v$v"
  git push origin "v$v"
  gh release create "v$v" --verify-tag --generate-notes ${pre[@]+"${pre[@]}"}
