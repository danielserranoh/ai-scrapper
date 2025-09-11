#!/usr/bin/env python3
"""
Simple CLI script for export operations as mentioned in README
"""

import sys
from main import main

if __name__ == '__main__':
    # This script simply delegates to main.py
    # Provides the interface mentioned in README: python cli.py export --job job_id --format csv
    sys.exit(main())