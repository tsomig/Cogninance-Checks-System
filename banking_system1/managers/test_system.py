#!/usr/bin/env python3
"""
Root-Level Test - Run from Project Root
=======================================

Usage: python test_system.py
"""

print("\n" + "="*70)
print("🧪 BANKING SYSTEM - QUICK TEST")
print("="*70)

# Test 1: Can we import?
print("\n[1/3] Testing imports...")
try:
    from intent_parser import IntentParser
    print("✅ intent_parser imported successfully")
except ImportError as e:
    print(f"❌ Failed to import intent_parser: {e}")
    print("\n💡 Make sure you're in the correct directory:")
    print("   C:\\Users\\georg\\chuck\\banking_system1")
    exit(1)

# Test 2: Can we create parser?
print("\n[2/3] Creating parser...")
try:
    parser = IntentParser()
    print("✅ IntentParser created successfully")
except Exception as e:
    print(f"❌ Failed to create parser: {e}")
    exit(1)

# Test 3: Can we parse commands?
print("\n[3/3] Testing command parsing...")

test_cases = [
    ("Issue check to Alice for $500", "ISSUE_CHECK"),
    ("Accept check from Bob", "ACCEPT_CHECK"),
    ("Deny check #123", "DENY_CHECK"),
    ("What's my balance?", "QUERY_BALANCE"),
    ("Show my checks", "QUERY_CHECKS"),
]

passed = 0
failed = 0

for cmd, expected_op in test_cases:
    try:
        intent = parser.parse(cmd)
        if intent.operation == expected_op:
            print(f"  ✅ '{cmd[:35]}...' → {expected_op}")
            passed += 1
        else:
            print(f"  ❌ '{cmd[:35]}...' → Expected {expected_op}, got {intent.operation}")
            failed += 1
    except Exception as e:
        print(f"  ❌ '{cmd[:35]}...' → Error: {e}")
        failed += 1

# Summary
print("\n" + "="*70)
print(f"📊 RESULTS: {passed} passed, {failed} failed")
print("="*70)

if failed == 0:
    print("🎉 All tests passed! Your system is working correctly.\n")
    print("Next steps:")
    print("  1. python chat.py           - Try the interactive chat")
    print("  2. python web_app.py        - Launch the web interface")
    print("  3. python view_database.py  - View stored data")
else:
    print(f"⚠️  {failed} test(s) failed. Please check the errors above.\n")

print()
