#!/bin/sh
# generate.py formats and lints the modules it writes, so nothing else to run.
exec uv run scripts/generate.py
