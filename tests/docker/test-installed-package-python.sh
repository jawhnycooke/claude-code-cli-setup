#!/bin/bash
set -e

echo "=== Testing Installed Python Package ==="
echo "Current directory: $(pwd)"
echo "Python environment: $(which python)"

# Activate the test environment
source test-env/bin/activate

echo "Python version: $(python --version)"
echo "Pip packages installed:"
pip list | grep claude-code-setup

echo ""
echo "=== Package Installation Verification ==="
echo "Claude setup executable: $(which claude-setup)"
echo "Python path: $PYTHONPATH"

# Check if the package is properly installed
python -c "import claude_code_setup; print(f'Package version: {claude_code_setup.__version__}')"

echo ""
echo "=== Test: Help Command ==="
echo "Running: claude-setup --help"
claude-setup --help

echo ""
echo "=== Test: Version Command ==="
echo "Running: claude-setup --version"
claude-setup --version

echo ""
echo "=== Test: List Command (Non-Interactive) ==="
echo "Running: claude-setup list --no-interactive"
claude-setup list --no-interactive

echo ""
echo "=== Test: Init Command (Quick Setup) ==="
echo "Running: claude-setup init --quick --test-dir ./test-dir --force"
claude-setup init --quick --test-dir ./test-dir --force

echo ""
echo "=== Verify Init Created Files ==="
if [ -d "./test-dir/.claude" ]; then
    echo "✓ .claude directory created"
    echo "Contents: $(ls -la ./test-dir/.claude/)"
    
    if [ -f "./test-dir/.claude/settings.json" ]; then
        echo "✓ settings.json created"
        echo "Settings content:"
        cat ./test-dir/.claude/settings.json | head -10
    else
        echo "✗ settings.json not found"
        exit 1
    fi
else
    echo "✗ .claude directory not created"
    exit 1
fi

echo ""
echo "=== Test: List Templates ==="
echo "Running: claude-setup list templates --test-dir ./test-dir --no-interactive"
claude-setup list templates --test-dir ./test-dir --no-interactive

echo ""
echo "=== Test: Add Template Command ==="
echo "Running: claude-setup add template python-optimization --test-dir ./test-dir"
claude-setup add template python-optimization --test-dir ./test-dir --force

echo ""
echo "=== Verify Template Installation ==="
if [ -f "./test-dir/.claude/commands/python/optimization.md" ]; then
    echo "✓ Template installed successfully"
    echo "Template content preview:"
    head -5 ./test-dir/.claude/commands/python/optimization.md
else
    echo "✗ Template not installed"
    exit 1
fi

echo ""
echo "=== Test: Add Permission Command ==="
echo "Running: claude-setup add permission 'Bash(docker:*)' --test-dir ./test-dir"
claude-setup add permission 'Bash(docker:*)' --test-dir ./test-dir --force

echo ""
echo "=== Verify Permission Addition ==="
if grep -q "docker" ./test-dir/.claude/settings.json; then
    echo "✓ Permission added successfully"
else
    echo "✗ Permission not added"
    exit 1
fi

echo ""
echo "=== Test: Hooks List ==="
echo "Running: claude-setup hooks list --test-dir ./test-dir --no-interactive"
claude-setup hooks list --test-dir ./test-dir --no-interactive

echo ""
echo "=== Test: Settings Command ==="
echo "Running: claude-setup settings show --test-dir ./test-dir --no-interactive"
claude-setup settings show --test-dir ./test-dir --no-interactive

echo ""
echo "=== Test: Update Command ==="
echo "Running: claude-setup update --dry-run --test-dir ./test-dir"
claude-setup update --dry-run --test-dir ./test-dir

echo ""
echo "=== Final Verification ==="
echo "Configuration directory structure:"
find ./test-dir/.claude -type f | sort

echo ""
echo "Settings file validation:"
python -c "
import json
with open('./test-dir/.claude/settings.json') as f:
    settings = json.load(f)
    print(f'Theme: {settings.get(\"theme\", \"unknown\")}')
    print(f'Permissions: {len(settings.get(\"permissions\", {}).get(\"allow\", []))} allowed')
    print(f'Auto updater: {settings.get(\"autoUpdaterStatus\", \"unknown\")}')
"

echo ""
echo "=== Success: All Python CLI tests passed! ==="
echo "✅ Package installation verified"
echo "✅ CLI commands functional" 
echo "✅ File operations working"
echo "✅ Settings management operational"
echo "✅ Template system functional"
echo "✅ Permission system working"