#!/usr/bin/env python3
"""
Test Runner Script for Log Analysis Automation Tool
Run this script to execute comprehensive tests for all modules
"""

import sys
from pathlib import Path

# Add development folder to path
sys.path.append(str(Path(__file__).parent / "development_folder" / "dev_and_test"))

from test_runner import TestRunner

if __name__ == "__main__":
    print("Starting Log Analysis Automation Tool Test Suite...")
    test_runner = TestRunner()
    test_runner.run_all_tests()
