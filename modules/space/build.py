#!/usr/bin/env python3
"""Run Mono Space from a source checkout."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from mono_space.build import main

if __name__ == '__main__':
    main()
