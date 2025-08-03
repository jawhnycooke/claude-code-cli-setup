#!/usr/bin/env python3
"""Pre-commit code review hook.

This hook performs automated code review checks before allowing commits.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_code_quality():
    """Run code quality checks on staged files."""
    # Get list of staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return True, "No staged files found"
    
    if not files or files == ['']:
        return True, "No files to review"
    
    issues = []
    
    # Check Python files
    python_files = [f for f in files if f.endswith('.py')]
    if python_files:
        # Check for common issues
        for file in python_files:
            if not Path(file).exists():
                continue
                
            with open(file, 'r') as f:
                content = f.read()
                
            # Basic checks
            if 'print(' in content and 'debug' not in file.lower():
                issues.append(f"{file}: Contains print statements")
            
            if 'TODO' in content or 'FIXME' in content:
                issues.append(f"{file}: Contains TODO/FIXME comments")
            
            if 'import *' in content:
                issues.append(f"{file}: Uses wildcard imports")
    
    if issues:
        return False, "\n".join(issues)
    
    return True, "All quality checks passed"


def main():
    """Main hook entry point."""
    # Check if hook is enabled
    if os.environ.get('SKIP_QUALITY_CHECK') == '1':
        print("Quality check skipped")
        sys.exit(0)
    
    success, message = check_code_quality()
    
    result = {
        "action": "allow" if success else "block",
        "message": f"Pre-commit review: {message}"
    }
    
    print(json.dumps(result))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()