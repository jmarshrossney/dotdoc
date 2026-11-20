# AGENTS.md

## Gotchas

- Tests that render skip without Graphviz's `dot` program, so a passing run without it proves little.
- markdown-exec writes a traceback into the page and the build still passes when a `python exec="on"` block in `docs/` raises; `tests/test_docs.py` is the only gate.
- `ruff format` reformats Python blocks in `docs/*.md`. To hide a line from the rendered source, mark every line of it with `# markdown-exec: hide`, since ruff may split a `;`-joined line.
- With `use_directory_urls = false`, previews only work under the `site_url` path (e.g. `/dotdoc/`), not on un-prefixed URLs or `site/*.html` opened as files.
- The README mirrors `docs/index.md`, with its drawing as static images: after changing the home page's example, run `just readme-images`.
- The uv-pre-commit rev and the `uv_build` range in `[build-system]` must stay in step; `just bump` does both.
- `.copier-answers.yml` is replayed by `copier update`: keep it committed and don't hand-edit it.
