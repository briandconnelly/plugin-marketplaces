#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4.23"]
# ///
"""Validate a user-hosted plugin marketplace (see references/validation.md)."""

from __future__ import annotations

import sys

from mpcheck.cli import main

if __name__ == "__main__":
    sys.exit(main())
