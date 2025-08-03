# Troubleshooting Guide

This guide helps resolve common issues with Claude Code Setup installation, configuration, and usage.

## Table of Contents

- [Installation Issues](#installation-issues)
- [CLI Execution Issues](#cli-execution-issues)
- [Configuration Problems](#configuration-problems)
- [Hook and Template Issues](#hook-and-template-issues)
- [Performance Issues](#performance-issues)
- [Environment-Specific Issues](#environment-specific-issues)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

## Installation Issues

### Command Not Found After Installation

**Symptoms**: `claude-setup: command not found` after pip install

**Solutions**:

```bash
# 1. Check if Python scripts directory is in PATH
echo $PATH | grep -E "(\.local/bin|Scripts)"

# 2. Find where pip installed the command
pip show -f claude-code-setup | grep claude-setup

# 3. Use full Python module path as workaround
python -m claude_code_setup.cli --version

# 4. Install with --user flag
pip install --user claude-code-setup

# 5. Use pipx for isolated installation
pipx install claude-code-setup

# 6. On macOS, add Python scripts to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Python Version Compatibility Issues

**Symptoms**: Import errors or syntax errors during installation

**Requirements**: Python 3.9+ is required

```bash
# Check current Python version
python --version

# Install with specific Python version
python3.9 -m pip install claude-code-setup

# Update Python if too old (macOS with Homebrew)
brew install python@3.11

# Update Python (Linux)
sudo apt update && sudo apt install python3.11
```

### Permission Denied During Installation

**Symptoms**: Permission errors when installing globally

**Solutions**:

```bash
# Use --user flag to install in user directory
pip install --user claude-code-setup

# Or use pipx for isolated installation
pipx install claude-code-setup

# On Linux/macOS, fix permissions
sudo chown -R $(whoami) ~/.local

# Alternative: use virtual environment
python -m venv claude-env
source claude-env/bin/activate  # Windows: claude-env\Scripts\activate
pip install claude-code-setup
```

### Missing Dependencies

**Symptoms**: Import errors for Rich, Click, Pydantic, etc.

**Solutions**:

```bash
# Reinstall with all dependencies
pip install --upgrade --force-reinstall claude-code-setup

# Install dependencies manually if needed
pip install click rich questionary pydantic pyfiglet halo

# Check for dependency conflicts
pip check

# Create clean environment
python -m venv fresh-env
source fresh-env/bin/activate
pip install claude-code-setup
```

## CLI Execution Issues

### Import Errors

**Symptoms**: `ModuleNotFoundError` or `ImportError` when running commands

**Solutions**:

```bash
# Check if package is properly installed
python -c "import claude_code_setup; print('OK')"

# Verify package location
pip show claude-code-setup

# Check PYTHONPATH
echo $PYTHONPATH

# Reinstall if corrupted
pip uninstall claude-code-setup
pip install claude-code-setup

# Use direct module execution
python -m claude_code_setup.cli --help
```

### Terminal Formatting Issues

**Symptoms**: Garbled output, missing colors, broken progress bars

**Solutions**:

```bash
# Check terminal capabilities
echo $TERM
tput colors

# Force color output
export FORCE_COLOR=1
claude-setup --help

# Disable colors if not supported
export NO_COLOR=1
claude-setup --help

# Use non-interactive mode for scripts
claude-setup list --no-interactive

# Update terminal (macOS)
# Use iTerm2 or update Terminal.app preferences
```

### Slow Command Execution

**Symptoms**: Commands take longer than expected to run

**Solutions**:

```bash
# Enable debug mode to see timing
claude-setup --debug list

# Check for network issues (if fetching remote templates)
ping github.com

# Clear Python cache
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Check disk space
df -h

# Run with minimal configuration
claude-setup list --no-interactive
```

## Configuration Problems

### Settings File Corruption

**Symptoms**: JSON parse errors when reading settings

**Solutions**:

```bash
# Backup and regenerate settings
cp ~/.claude/settings.json ~/.claude/settings.json.backup
claude-setup init --force

# Validate JSON manually
python -m json.tool ~/.claude/settings.json

# Reset to defaults
rm ~/.claude/settings.json
claude-setup init --quick

# Repair specific issues
claude-setup settings show --debug
```

### Permission Denied for Configuration Directory

**Symptoms**: Cannot create or modify `.claude` directory

**Solutions**:

```bash
# Check directory permissions
ls -la ~/.claude
ls -la ./.claude

# Fix permissions
chmod 755 ~/.claude
chmod 644 ~/.claude/settings.json

# Use test directory as workaround
claude-setup init --test-dir ./temp-config

# Change ownership (Linux/macOS)
sudo chown -R $(whoami) ~/.claude
```

### Configuration Not Found

**Symptoms**: Commands report "Configuration not found"

**Solutions**:

```bash
# Initialize configuration
claude-setup init

# Check current directory for local config
ls -la .claude

# Use global configuration
claude-setup init --global

# Specify test directory
claude-setup --test-dir /path/to/config list

# Debug configuration loading
claude-setup settings show --debug
```

## Hook and Template Issues

### Hook Execution Failures

**Symptoms**: Hooks not triggering or failing with errors

**Solutions**:

```bash
# Check hook status
claude-setup hooks status

# List installed hooks
claude-setup hooks list

# Reinstall problematic hook
claude-setup hooks remove file-change-limiter
claude-setup hooks add file-change-limiter

# Check hook dependencies
python -c "import sys; print(sys.executable)"

# Verify hook permissions
ls -la ~/.claude/hooks/*/

# Test hook manually
python ~/.claude/hooks/security/file-change-limiter/limit_file_changes.py
```

### Template Installation Failures

**Symptoms**: Templates fail to install or render incorrectly

**Solutions**:

```bash
# Check available templates
claude-setup list templates --debug

# Force reinstall template
claude-setup add template python-optimization --force

# Check template file permissions
ls -la ~/.claude/commands/*/

# Validate template format
cat ~/.claude/commands/python/optimization.md

# Clear template cache (if any)
rm -rf ~/.claude/commands/
claude-setup add template python-optimization
```

### Hook Dependencies Missing

**Symptoms**: Hooks fail with missing module errors

**Solutions**:

```bash
# Install hook-specific dependencies
# For AWS hooks
pip install boto3

# For file watching hooks
pip install watchdog

# For validation hooks
pip install jsonschema

# Check which Python interpreter hooks use
head -1 ~/.claude/hooks/*/metadata.json

# Update hook configuration
claude-setup hooks remove problematic-hook
claude-setup hooks add problematic-hook
```

## Performance Issues

### Slow Template Processing

**Symptoms**: Template operations take a long time

**Solutions**:

```bash
# Use uv for faster operations
uv pip install claude-code-setup

# Clear Python cache
find ~/.claude -name "*.pyc" -delete
find ~/.claude -name "__pycache__" -type d -exec rm -rf {} +

# Check available memory
free -h  # Linux
vm_stat  # macOS

# Use smaller batch sizes
claude-setup add template one-at-a-time

# Profile performance
claude-setup --debug add template python-optimization
```

### High Memory Usage

**Symptoms**: System becomes slow during claude-setup operations

**Solutions**:

```bash
# Monitor memory usage
top -p $(pgrep -f claude-setup)

# Use non-interactive mode
claude-setup list --no-interactive

# Process templates individually
for template in template1 template2; do
    claude-setup add template $template
done

# Check for memory leaks
claude-setup settings show
sleep 5
claude-setup settings show
```

### Network-Related Slowdowns

**Symptoms**: Commands hang or timeout

**Solutions**:

```bash
# Test network connectivity
ping github.com

# Use offline mode (if available)
claude-setup list templates --no-interactive

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Configure git (if templates use git)
git config --global http.timeout 30
```

## Environment-Specific Issues

### Windows-Specific Issues

**Symptoms**: Path issues, permission errors, PowerShell compatibility

**Solutions**:

```powershell
# Use PowerShell as Administrator
# Add Python Scripts to PATH
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"

# Use full path if command not found
python -m claude_code_setup.cli --version

# Fix line ending issues
git config --global core.autocrlf true

# Use Windows Subsystem for Linux (WSL) as alternative
wsl
pip install claude-code-setup
claude-setup --version
```

### macOS-Specific Issues

**Symptoms**: SIP restrictions, Homebrew conflicts, terminal app issues

**Solutions**:

```bash
# Use Homebrew Python
brew install python@3.11
/opt/homebrew/bin/python3.11 -m pip install claude-code-setup

# Add to PATH in ~/.zshrc
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Use iTerm2 for better terminal support
brew install --cask iterm2

# Fix macOS permission issues
xattr -d com.apple.quarantine ~/.claude/hooks/*/
```

### Linux Distribution Issues

**Symptoms**: Package manager conflicts, missing system libraries

**Solutions**:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv

# CentOS/RHEL/Fedora
sudo dnf install python3.11 python3.11-pip

# Arch Linux
sudo pacman -S python python-pip

# Use distribution package manager
# Debian/Ubuntu
sudo apt install python3-claude-code-setup  # if available

# Use pyenv for Python version management
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv global 3.11.0
```

### Docker/Container Issues

**Symptoms**: Permission issues, missing dependencies in containers

**Solutions**:

```dockerfile
# Dockerfile for claude-setup
FROM python:3.11-slim

RUN pip install claude-code-setup

# Set working directory
WORKDIR /workspace

# Create non-root user
RUN useradd -m claude
USER claude

# Set HOME directory for .claude config
ENV HOME=/home/claude

CMD ["claude-setup", "--help"]
```

```bash
# Run with volume mount for config
docker run -v $(pwd)/.claude:/home/claude/.claude claude-setup:latest
```

### CI/CD Environment Issues

**Symptoms**: Non-interactive environments, permission issues

**Solutions**:

```yaml
# GitHub Actions example
- name: Install claude-setup
  run: |
    pip install claude-code-setup
    claude-setup init --quick --no-interactive
    
- name: Setup templates
  run: |
    claude-setup add template python-optimization --force --no-interactive
```

```bash
# General CI script
export NO_COLOR=1
pip install claude-code-setup
claude-setup init --quick --no-interactive --force
claude-setup list templates --no-interactive
```

## Debug Mode

### Enabling Debug Output

```bash
# Enable debug mode for any command
claude-setup --debug init

# Check debug output for specific operations
claude-setup --debug settings show

# Debug template processing
claude-setup --debug add template python-optimization

# Debug hook execution
claude-setup --debug hooks add file-change-limiter
```

### Logging Configuration

```bash
# Check log output location
claude-setup --debug settings show 2>&1 | grep -i log

# Increase verbosity
export CLAUDE_DEBUG=1
claude-setup settings show

# Save debug output to file
claude-setup --debug init > debug.log 2>&1
```

### Common Debug Information

Debug output includes:
- Configuration file locations
- Template and hook registry loading
- File permission checks
- Network requests (if any)
- Error stack traces
- Performance timing information

## Getting Help

### Self-Diagnosis Commands

```bash
# System information
claude-setup --version
python --version
pip --version

# Configuration check
claude-setup settings show --debug

# Installation verification
pip show claude-code-setup

# Template and hook status
claude-setup list --no-interactive
claude-setup hooks status
```

### Collecting Information for Bug Reports

```bash
# Create comprehensive system report
{
    echo "=== System Information ==="
    uname -a
    python --version
    pip --version
    claude-setup --version
    
    echo -e "\n=== Installation Details ==="
    pip show claude-code-setup
    which claude-setup
    
    echo -e "\n=== Configuration ==="
    claude-setup settings show --debug
    
    echo -e "\n=== Environment ==="
    env | grep -E "(PYTHON|PATH|CLAUDE)"
} > bug-report.txt
```

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/jawhnycooke/claude-code-setup/issues)
- **Documentation**: [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete command reference
- **Migration Guide**: [MIGRATION.md](MIGRATION.md) for upgrading from TypeScript version

### Professional Support

For enterprise users or complex deployment issues:
- Check the repository for professional support contacts
- Consider contributing back fixes for common issues
- Document custom solutions for your environment

Remember to always include:
- Operating system and version
- Python version
- Complete error messages
- Steps to reproduce the issue
- Your configuration (without sensitive data)