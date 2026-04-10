# Contributing to smartest-tv

## Quick start

```bash
git clone https://github.com/Hybirdss/smartest-tv.git
cd smartest-tv
pip install -e ".[dev]"
python -m pytest tests/ -v
```

No TV required. All tests use mocks.

## Submitting a PR

1. Fork and create a branch from `main`
2. Make your changes
3. Run tests: `python -m pytest tests/ -v`
4. Run lint: `ruff check src/`
5. Open a PR — CodeRabbit will review automatically

## Adding a TV driver

See [docs/contributing/driver-development.md](docs/contributing/driver-development.md) for the full guide. In short:

1. Create `src/smartest_tv/drivers/yourplatform.py` implementing `TVDriver` ABC
2. Add platform detection to `src/smartest_tv/discovery.py`
3. Register in `src/smartest_tv/drivers/factory.py`
4. Add tests in `tests/`

## Contributing cache entries

See [docs/contributing/cache-contributions.md](docs/contributing/cache-contributions.md). Add entries to `community-cache.json` — the `validate-cache` CI job checks structure automatically.

## Code style

- Python 3.11+, type hints everywhere
- `ruff` for linting (CI enforced)
- Commit messages: imperative mood, explain *why*

## CLA

First-time contributors are asked to sign a one-time CLA via a PR comment.
