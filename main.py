#!/usr/bin/env python3
"""
A utility for compiling LaTeX documents and generating diffs between Git revisions.
"""

import sys

from latex_builder.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
