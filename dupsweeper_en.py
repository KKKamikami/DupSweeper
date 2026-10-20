#!/usr/bin/env python3
"""English-language DupSweeper entry point for a dedicated Windows executable."""
import multiprocessing as mp
import sys
from dupsweeper import run_app, self_test
if __name__ == '__main__':
    mp.freeze_support()
    if '--self-test' in sys.argv:
        self_test()
    else:
        run_app('en')
