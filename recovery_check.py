#!/usr/bin/env python3
"""Recovery script to check and restore repository state"""

import subprocess
import os
from pathlib import Path
import sys

# Force UTF-8 output for stderr as well
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.chdir(r'd:\axiomcode')

print("=" * 60)
print("REPOSITORY RECOVERY DIAGNOSTIC")
print("=" * 60)

# Check git status
print("\n1. Git Status:")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, timeout=10)
if result.stdout:
    print(result.stdout)
else:
    print("   [OK] Working directory clean")

# Check for untracked files
print("\n2. Untracked Files:")
result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], capture_output=True, text=True, timeout=10)
if result.stdout:
    print(result.stdout)
else:
    print("   [OK] No untracked files")

# List all tracked files
print("\n3. Currently Tracked Files in Root:")
result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, timeout=10)
files = result.stdout.strip().split('\n')
root_files = [f for f in files if '/' not in f]
for f in sorted(root_files):
    print(f"   - {f}")

# Check for missing files that should exist
print("\n4. Expected Files Check:")
expected_files = [
    'AXIOMCODE_API_REFERENCE.py',
    'AXIOMCODE_USER_GUIDE.md',
    'cli.py',
    'README.md',
    'pyproject.toml'
]

for fname in expected_files:
    path = Path(fname)
    status = "[OK]" if path.exists() else "[MISSING]"
    print(f"   {fname}: {status}")

# Check git log for deleted files
print("\n5. Recently Deleted Files:")
result = subprocess.run(['git', 'log', '--diff-filter=D', '--summary', '-1', '--name-only'], 
                       capture_output=True, text=True, timeout=10)
if result.stdout:
    print(result.stdout)
else:
    print("   [OK] No recent deletions")

print("\n" + "=" * 60)
print("RECOVERY STATUS: Complete")
print("=" * 60)
