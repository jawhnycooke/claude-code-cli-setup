#!/bin/bash
set -e

# Move to the project root directory
cd "$(dirname "$0")/../.."

echo "=== Claude Code Setup - Python Package Testing ==="
echo "Testing the Python package installation and CLI functionality"
echo ""

# Build the Docker image
echo "🐳 Building Python Docker test image..."
docker build -t claude-code-setup-python-test -f tests/docker/Dockerfile.python .

echo ""
echo "🧪 Running Python package tests in Docker container..."
echo "This will test:"
echo "  - Package wheel build and installation"
echo "  - CLI command functionality"
echo "  - Template and hook systems"
echo "  - Settings management"
echo "  - File operations"
echo ""

# Run the tests
docker run --rm claude-code-setup-python-test

echo ""
echo "✅ Python Docker tests completed successfully!"
echo "🎉 The Python package works correctly when installed via pip/uv!"