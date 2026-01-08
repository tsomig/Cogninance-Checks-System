#!/usr/bin/env python3
"""
System Diagnostic - Check Your Setup
====================================

Run this to diagnose any issues with your project setup.
Usage: python diagnose.py
"""

import os
import sys

print("\n" + "="*70)
print("🔍 BANKING SYSTEM - DIAGNOSTIC CHECK")
print("="*70)

# Check 1: Current directory
print("\n[1] Current Directory:")
cwd = os.getcwd()
print(f"    {cwd}")

# Check 2: Python version
print("\n[2] Python Version:")
print(f"    {sys.version}")

# Check 3: Required files
print("\n[3] Required Files:")
required_files = [
    'intent_parser.py',
    'check_manager.py',
    'transaction_manager.py',
    'conversation_agent.py',
    'schema.py',
    'config.py',
    'chat.py',
    'web_app.py',
]

all_present = True
for filename in required_files:
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"    {status} {filename}")
    if not exists:
        all_present = False

if not all_present:
    print("\n⚠️  Some files are missing!")
    print("    Make sure you're in the project root directory:")
    print("    cd C:\\Users\\georg\\chuck\\banking_system1")
    print("\n    Or check if you have all the project files.")

# Check 4: Can we import?
print("\n[4] Import Test:")
if all_present:
    try:
        from intent_parser import IntentParser
        print("    ✅ intent_parser imports successfully")
        
        parser = IntentParser()
        print("    ✅ IntentParser instantiates successfully")
        
        intent = parser.parse("Test command")
        print("    ✅ IntentParser.parse() works")
        
        print("\n🎉 Everything looks good!")
        
    except Exception as e:
        print(f"    ❌ Import/execution failed: {e}")
        print("\n    This might be a Python environment issue.")
else:
    print("    ⏭️  Skipped (files missing)")

# Check 5: Tests directory
print("\n[5] Tests Directory:")
if os.path.exists('tests'):
    print("    ✅ tests/ directory exists")
    test_files = [f for f in os.listdir('tests') if f.endswith('.py')]
    if test_files:
        print(f"    Found {len(test_files)} test file(s):")
        for tf in test_files:
            print(f"      - {tf}")
    else:
        print("    ⚠️  tests/ directory is empty")
else:
    print("    ❌ tests/ directory not found")
    print("    Create it with: mkdir tests")

# Check 6: Database
print("\n[6] Database:")
if os.path.exists('banking_system.db'):
    size = os.path.getsize('banking_system.db')
    print(f"    ✅ banking_system.db exists ({size:,} bytes)")
else:
    print("    ℹ️  No database yet (this is OK)")
    print("    Run 'python chat.py' to create one")

# Summary
print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)

if all_present:
    print("✅ Your project setup looks correct!")
    print("\nTo test the system:")
    print("  1. Run: python test_system.py")
    print("  2. If that works, try: python chat.py")
    print("  3. Then view data with: python view_database.py")
else:
    print("⚠️  Your project setup has issues.")
    print("\nPlease check:")
    print("  1. Are you in the correct directory?")
    print("     cd C:\\Users\\georg\\chuck\\banking_system1")
    print("  2. Do you have all project files?")
    print("  3. Did you download everything from the outputs folder?")

print("\n" + "="*70 + "\n")
