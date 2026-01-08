#!/usr/bin/env python3
"""
Test Runner - Execute All Test Suites
=====================================

Runs all unit and integration tests and provides summary.
"""

import sys
import os

# Add test environment to path
sys.path.insert(0, '/home/claude/test_env')

# Import from the test directory
sys.path.insert(0, '/home/claude')

from tests.test_intent_parser import TestIntentParser
from tests.test_check_manager import TestCheckManager
from tests.test_integration import TestIntegration


def print_header():
    """Print test suite header"""
    print("\n" + "="*70)
    print("🧪 CONVERSATIONAL BANKING SYSTEM - COMPLETE TEST SUITE")
    print("="*70)
    print("\nRunning comprehensive tests on all system components...")
    print("This includes: Intent Parser, Check Manager, and Integration Tests")
    print("="*70)


def print_final_summary(results):
    """Print final summary of all tests"""
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_tests = sum(r['total'] for r in results)
    
    print("\n\n" + "="*70)
    print("📊 FINAL TEST SUMMARY")
    print("="*70)
    
    # Individual suite results
    for result in results:
        status = "✅ PASS" if result['failed'] == 0 else "❌ FAIL"
        print(f"\n{result['suite_name']}: {status}")
        print(f"  Tests: {result['total']} | Passed: {result['passed']} | Failed: {result['failed']}")
    
    # Overall results
    print("\n" + "-"*70)
    print("OVERALL RESULTS:")
    print(f"  Total Tests Run: {total_tests}")
    print(f"  ✅ Total Passed: {total_passed}")
    print(f"  ❌ Total Failed: {total_failed}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"  Success Rate: {success_rate:.1f}%")
    print("="*70)
    
    if total_failed == 0:
        print("\n🎉 🎉 🎉 ALL TESTS PASSED! 🎉 🎉 🎉")
        print("\nYour conversational banking system is working perfectly!")
    else:
        print(f"\n⚠️  WARNING: {total_failed} test(s) failed")
        print("Please review the test output above for details.")
    
    print("\n" + "="*70 + "\n")
    
    return total_failed == 0


def main():
    """Run all test suites"""
    print_header()
    
    results = []
    all_passed = True
    
    # Test 1: Intent Parser
    print("\n" + "▶"*35)
    print("SUITE 1/3: Intent Parser Tests")
    print("▶"*35)
    try:
        tester1 = TestIntentParser()
        suite1_passed = tester1.run_all_tests()
        results.append({
            'suite_name': 'Intent Parser',
            'passed': tester1.passed,
            'failed': tester1.failed,
            'total': tester1.tests_run
        })
        if not suite1_passed:
            all_passed = False
    except Exception as e:
        print(f"\n❌ Intent Parser tests crashed: {e}")
        all_passed = False
        results.append({
            'suite_name': 'Intent Parser',
            'passed': 0,
            'failed': 1,
            'total': 1
        })
    
    # Test 2: Check Manager
    print("\n\n" + "▶"*35)
    print("SUITE 2/3: Check Manager Tests")
    print("▶"*35)
    try:
        tester2 = TestCheckManager()
        suite2_passed = tester2.run_all_tests()
        tester2.cleanup()
        results.append({
            'suite_name': 'Check Manager',
            'passed': tester2.passed,
            'failed': tester2.failed,
            'total': tester2.tests_run
        })
        if not suite2_passed:
            all_passed = False
    except Exception as e:
        print(f"\n❌ Check Manager tests crashed: {e}")
        all_passed = False
        results.append({
            'suite_name': 'Check Manager',
            'passed': 0,
            'failed': 1,
            'total': 1
        })
    
    # Test 3: Integration
    print("\n\n" + "▶"*35)
    print("SUITE 3/3: Integration Tests")
    print("▶"*35)
    try:
        tester3 = TestIntegration()
        suite3_passed = tester3.run_all_tests()
        tester3.cleanup()
        results.append({
            'suite_name': 'Integration',
            'passed': tester3.passed,
            'failed': tester3.failed,
            'total': tester3.tests_run
        })
        if not suite3_passed:
            all_passed = False
    except Exception as e:
        print(f"\n❌ Integration tests crashed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
        results.append({
            'suite_name': 'Integration',
            'passed': 0,
            'failed': 1,
            'total': 1
        })
    
    # Final summary
    final_passed = print_final_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if final_passed else 1)


if __name__ == "__main__":
    main()
