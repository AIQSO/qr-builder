# Contributing to qr-builder

Thanks for your interest! This project welcomes issues, bug fixes, and feature PRs.

## Development setup

```bash
git clone https://github.com/AIQSO/qr-builder.git
cd qr-builder
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quality gates (run before opening a PR)

```bash
ruff check qr_builder/          # lint
mypy qr_builder/                # type check
pytest --cov=qr_builder         # tests + coverage
pip-audit                       # CVE scan
deptry .                        # dependency hygiene
```

CI runs these on every push and PR. A failing audit or test will block merge.

## Branching and commits

- Branch from `main`: `git checkout -b feat/my-change`
- Keep PRs focused — one concern per PR
- Use [Conventional Commits](https://www.conventionalcommits.org/) style: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`
- Update `CHANGELOG.md` under an `## [Unreleased]` section

## Adding a dependency

1. Add it to `pyproject.toml` under `dependencies` (runtime) or `optional-dependencies.dev` (tooling)
2. Re-run `pip install -e ".[dev]"` and `pip-audit` — confirm no new CVEs
3. Document *why* the dependency is needed in the PR description

## Reporting security issues

See [SECURITY.md](SECURITY.md). **Do not** open public issues for security bugs.

## Release process (maintainers)

1. Update `version` in `pyproject.toml` and note changes in `CHANGELOG.md`
2. Commit: `chore(release): v0.x.y`
3. Tag: `git tag v0.x.y && git push origin v0.x.y`
4. The `publish.yml` workflow builds and publishes to PyPI + ghcr.io
