name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install FFmpeg (required by pydub)
        run: sudo apt-get update && sudo apt-get install -y ffmpeg

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run Ruff linter
        run: uv run ruff check .

      - name: Run Ruff formatter check
        run: uv run ruff format --check .

      - name: Run tests with pytest
        run: uv run pytest --cov=audio_splitter --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false