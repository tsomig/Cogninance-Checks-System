#!/usr/bin/env python3
"""
Test Setup - Prepare Project Structure
======================================

Sets up the proper directory structure for running tests.
"""

import os
import shutil

print("📦 Setting up test environment...")

# Create directory structure
test_root = "/home/claude/test_env"
if os.path.exists(test_root):
    shutil.rmtree(test_root)

os.makedirs(f"{test_root}/managers", exist_ok=True)
os.makedirs(f"{test_root}/database", exist_ok=True)

# Copy files to proper structure
project_files = {
    'intent_parser.py': 'managers/',
    'check_manager.py': 'managers/',
    'transaction_manager.py': 'managers/',
    'conversation_agent.py': 'managers/',
    'schema.py': 'database/',
    'config.py': '',
}

for filename, subdir in project_files.items():
    src = f"/mnt/project/{filename}"
    dst = f"{test_root}/{subdir}{filename}"
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"  ✅ Copied {filename} to {subdir or 'root'}")

# Create __init__.py files
with open(f"{test_root}/__init__.py", 'w') as f:
    pass
with open(f"{test_root}/managers/__init__.py", 'w') as f:
    pass
with open(f"{test_root}/database/__init__.py", 'w') as f:
    pass

print("\n✅ Test environment ready at /home/claude/test_env")
print("Run tests with: python /home/claude/tests/run_all_tests.py")
