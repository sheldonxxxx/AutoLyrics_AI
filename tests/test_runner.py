#!/usr/bin/env python3
"""
Test runner script to execute all tests for the music lyrics processing pipeline.
"""

import unittest
import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def discover_and_run_tests(test_pattern="test_*.py", verbosity=2):
    """
    Discover and run all tests matching the pattern.

    Args:
        test_pattern (str): Pattern to match test files
        verbosity (int): Verbosity level for test output

    Returns:
        unittest.TestResult: Results of test execution
    """
    # Discover all test files in tests directory
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern=test_pattern)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    return result

def run_specific_test_module(module_name, verbosity=2):
    """
    Run tests for a specific module.

    Args:
        module_name (str): Name of the test module to run (e.g., 'test_utils')
        verbosity (int): Verbosity level for test output

    Returns:
        unittest.TestResult: Results of test execution
    """
    # Load specific test module from tests directory
    loader = unittest.TestLoader()
    # Add tests directory to path for module loading
    test_module_path = f"tests.{module_name}"
    suite = loader.loadTestsFromName(test_module_path)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    return result

def main():
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description='Run tests for the music lyrics processing pipeline'
    )

    parser.add_argument(
        '--module', '-m',
        help='Run tests for a specific module (e.g., test_utils, test_extract_metadata)'
    )

    parser.add_argument(
        '--pattern', '-p',
        default='test_*.py',
        help='Pattern to match test files (default: test_*.py)'
    )

    parser.add_argument(
        '--verbosity', '-v',
        type=int,
        default=2,
        choices=[0, 1, 2],
        help='Verbosity level: 0=quiet, 1=normal, 2=verbose (default: 2)'
    )

    parser.add_argument(
        '--list-tests', '-l',
        action='store_true',
        help='List all available tests without running them'
    )

    args = parser.parse_args()

    print("Music Lyrics Processing Pipeline - Test Suite (tests/)")
    print("=" * 55)

    if args.list_tests:
        # List all available tests in tests directory
        loader = unittest.TestLoader()
        start_dir = Path(__file__).parent
        suite = loader.discover(start_dir, pattern=args.pattern)

        print("Available test modules:")
        for test_group in suite:
            for test_case in test_group:
                module_name = test_case._tests[0].__class__.__module__
                # Extract just the filename without the full path
                if '.' in module_name:
                    module_name = module_name.split('.')[-1]
                print(f"  - {module_name}")
                break

        return 0

    try:
        if args.module:
            # Run specific test module
            print(f"Running tests for module: tests/{args.module}")
            result = run_specific_test_module(args.module, args.verbosity)
        else:
            # Run all tests
            print("Running all tests in tests/ directory...")
            result = discover_and_run_tests(args.pattern, args.verbosity)

        # Print summary
        print("\n" + "=" * 55)
        print("Test Summary:")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

        # Return appropriate exit code
        if result.failures or result.errors:
            print("\n❌ Some tests failed or had errors!")
            return 1
        else:
            print("\n✅ All tests passed!")
            return 0

    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())