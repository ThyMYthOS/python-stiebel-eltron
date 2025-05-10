#!/bin/sh

uv run scripts/generate.py
uvx ruff format pystiebeleltron
