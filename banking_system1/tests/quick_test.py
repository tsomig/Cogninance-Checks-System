#!/usr/bin/env python3
"""
Simple Test Runner - Windows Compatible
=======================================

Runs a quick test of the intent parser.
No complex imports or directory structures needed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from intent_parser import IntentParser
    
    print("\n" + "="*70)
    print("🧪 QUICK INTENT PARSER TEST")
    print("="*70)
    
    parser = IntentParser()
    
    test_cases = [
        ("Issue check to Alice for $500", "ISSUE_CHECK", 500.0, "Alice"),
        ("Accept check from Bob", "ACCEPT_CHECK", None, "Bob"),
        ("Deny check #123", "DENY_CHECK", None, None),
        ("Forward check #456 to Charlie", "FORWARD_CHECK", None, "Charlie"),
        ("What's my balance?", "QUERY_BALANCE", None, None),
        ("Show my checks", "QUERY_CHECKS", None, None),
    ]
    
    passed = 0
    failed = 0
    
    for user_input, expected_op, expected_amt, expected_party in test_cases:
        intent = parser.parse(user_input)
        
        if intent.operation == expected_op:
            print(f"✅ '{user_input[:40]}' -> {expected_op}")
            passed += 1
        else:
            print(f"❌ '{user_input[:40]}' -> Expected {expected_op}, got {intent.operation}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("🎉 All tests passed!\n")
    else:
        print(f"⚠️  {failed} test(s) failed\n")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nMake sure you're in the project root directory:")
    print("  cd C:\\Users\\georg\\chuck\\banking_system1")
    print("  python tests\\quick_test.py")
    sys.exit(1)
