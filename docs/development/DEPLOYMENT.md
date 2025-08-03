# Deployment Guide

This guide covers packaging, distributing, and deploying Claude Code Setup for various environments and use cases.

## Table of Contents

- [Building from Source](#building-from-source)
- [Creating Distribution Packages](#creating-distribution-packages)
- [PyPI Publishing](#pypi-publishing)
- [Docker Deployment](#docker-deployment)
- [CI/CD Integration](#cicd-integration)
- [Enterprise Distribution](#enterprise-distribution)
- [Development Deployment](#development-deployment)

## Building from Source

### Prerequisites

```bash
# Required tools
python3.9+
uv (recommended) or pip
git
build (for packaging)

# Install build dependencies
uv pip install build twine wheel setuptools
# Or with pip
pip install build twine wheel setuptools
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/jawhnycooke/claude-code-setup.git
cd claude-code-setup

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .
uv pip install -r requirements-dev.txt

# Verify installation
claude-setup --version
```

### Building the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build source distribution and wheel
uv run python -m build

# Verify build artifacts
ls dist/
# Should show:
# claude_code_setup-X.X.X-py3-none-any.whl
# claude-code-setup-X.X.X.tar.gz
```

### Build Verification

```bash
# Test wheel installation in clean environment
uv venv test-env
source test-env/bin/activate
uv pip install dist/claude_code_setup-*.whl

# Verify functionality
claude-setup --version
claude-setup init --quick --test-dir ./test-config --force
claude-setup list templates --no-interactive

# Clean up
deactivate
rm -rf test-env test-config
```

## Creating Distribution Packages

### Wheel Distribution

```bash
# Create wheel for current platform
python -m build --wheel

# Create universal wheel (Python-only package)
python setup.py bdist_wheel --universal

# Verify wheel contents
unzip -l dist/claude_code_setup-*.whl | head -20
```

### Source Distribution

```bash
# Create source distribution
python -m build --sdist

# Verify source package contents
tar -tzf dist/claude-code-setup-*.tar.gz | head -20
```

### Cross-Platform Considerations

```bash
# Package includes platform-independent Python code
# No special handling needed for different OS

# Verify cross-platform compatibility
python -c "
import claude_code_setup
print('Package imports successfully')
print(f'Version: {claude_code_setup.__version__}')
"
```

## PyPI Publishing

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ claude-code-setup

# Verify installation
claude-setup --version
```

### Production PyPI

```bash
# Configure PyPI credentials (one-time setup)
# Option 1: Use token (recommended)
echo "[pypi]
username = __token__
password = pypi-your-api-token-here" > ~/.pypirc

# Option 2: Use username/password
echo "[pypi]
username = your-username
password = your-password" > ~/.pypirc

# Upload to production PyPI
twine upload dist/*

# Verify public installation
pip install claude-code-setup
claude-setup --version
```

### Automated Publishing

```bash
# Create release script
cat > release.sh << 'EOF'
#!/bin/bash
set -e

# Validate version
VERSION=$(python -c "import claude_code_setup; print(claude_code_setup.__version__)")
echo "Releasing version $VERSION"

# Clean and build
rm -rf dist/ build/ *.egg-info/
python -m build

# Upload to Test PyPI first
twine upload --repository testpypi dist/*
echo "Uploaded to Test PyPI"

# Wait for user confirmation
read -p "Test PyPI upload successful. Upload to production PyPI? (y/N): " confirm
if [[ $confirm == [yY] ]]; then
    twine upload dist/*
    echo "Released to production PyPI"
else
    echo "Skipped production upload"
fi
EOF

chmod +x release.sh
```

### Version Management

```bash
# Update version in pyproject.toml
# version = "X.Y.Z"

# Tag release
git tag v$VERSION
git push origin v$VERSION

# Create GitHub release (if using GitHub)
gh release create v$VERSION dist/* --title "Release $VERSION" --notes "Release notes here"
```

## Docker Deployment

### Basic Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install claude-setup
RUN pip install claude-code-setup

# Create non-root user
RUN useradd -m -s /bin/bash claude
USER claude
WORKDIR /home/claude

# Set up environment
ENV HOME=/home/claude
ENV PATH="/home/claude/.local/bin:$PATH"

# Default command
CMD ["claude-setup", "--help"]
```

### Multi-stage Build

```dockerfile
# Multi-stage Dockerfile for optimized size
FROM python:3.11-slim as builder

# Install build dependencies
RUN pip install build

# Copy source code
COPY . /src
WORKDIR /src

# Build package
RUN python -m build

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install wheel from builder stage
COPY --from=builder /src/dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Create non-root user
RUN useradd -m claude
USER claude
WORKDIR /home/claude

CMD ["claude-setup", "--help"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-setup:
    build: .
    volumes:
      - ./workspace:/home/claude/workspace
      - claude-config:/home/claude/.claude
    environment:
      - CLAUDE_ENV=production
    working_dir: /home/claude/workspace
    command: ["claude-setup", "interactive"]

  # Development service
  claude-setup-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/src
      - ./workspace:/home/claude/workspace
    environment:
      - CLAUDE_DEBUG=1
    working_dir: /src
    command: ["bash"]

volumes:
  claude-config:
```

### Container Registry Publishing

```bash
# Build and tag
docker build -t claude-code-setup:latest .
docker tag claude-code-setup:latest yourregistry/claude-code-setup:v$(cat pyproject.toml | grep version | cut -d'"' -f2)

# Push to registry
docker push yourregistry/claude-code-setup:latest
docker push yourregistry/claude-code-setup:v$(cat pyproject.toml | grep version | cut -d'"' -f2)

# Or use buildx for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t yourregistry/claude-code-setup:latest --push .
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest tests/ -v
    
    - name: Run linting
      run: |
        ruff check src/ tests/
        black --check src/ tests/
        mypy src/

  build-and-publish:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install build dependencies
      run: pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
    
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        generate_release_notes: true

  docker-build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=tag
          type=raw,value=latest
    
    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

test:
  stage: test
  image: python:3.11
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.9", "3.10", "3.11", "3.12"]
  before_script:
    - pip install -e .
    - pip install -r requirements-dev.txt
  script:
    - pytest tests/ -v
    - ruff check src/ tests/
    - black --check src/ tests/
    - mypy src/

build:
  stage: build
  image: python:3.11
  script:
    - pip install build
    - python -m build
  artifacts:
    paths:
      - dist/
    expire_in: 1 hour

deploy-pypi:
  stage: deploy
  image: python:3.11
  dependencies:
    - build
  script:
    - pip install twine
    - twine upload dist/*
  only:
    - tags
  variables:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: $CI_PYPI_TOKEN

deploy-docker:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
  only:
    - tags
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PYPI_CREDENTIALS = credentials('pypi-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -e .
                    pip install -r requirements-dev.txt
                '''
            }
        }
        
        stage('Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ --junitxml=test-results.xml
                    ruff check src/ tests/
                    black --check src/ tests/
                    mypy src/
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }
        
        stage('Build') {
            steps {
                sh '''
                    . venv/bin/activate
                    pip install build
                    python -m build
                '''
            }
            post {
                success {
                    archiveArtifacts artifacts: 'dist/*', fingerprint: true
                }
            }
        }
        
        stage('Deploy') {
            when {
                tag pattern: "v.*", comparator: "REGEXP"
            }
            steps {
                sh '''
                    . venv/bin/activate
                    pip install twine
                    twine upload dist/* -u __token__ -p $PYPI_CREDENTIALS
                '''
            }
        }
    }
}
```

## Enterprise Distribution

### Private PyPI Server

```bash
# Set up private PyPI server (example with devpi)
pip install devpi-server devpi-client

# Start server
devpi-server --start --host=localhost --port=3141

# Configure client
devpi use http://localhost:3141
devpi login admin --password ''
devpi index -c mycompany/dev

# Upload to private server
devpi upload dist/*

# Install from private server
pip install -i http://localhost:3141/mycompany/dev claude-code-setup
```

### Internal Distribution

```bash
# Create internal package repository
mkdir -p /shared/packages/claude-code-setup
cp dist/* /shared/packages/claude-code-setup/

# Install from shared location
pip install /shared/packages/claude-code-setup/claude_code_setup-*.whl

# Or create simple index
cd /shared/packages
python -m http.server 8080

# Install from local index
pip install --index-url http://internal-server:8080/simple claude-code-setup
```

### Air-Gapped Environments

```bash
# Create offline bundle
mkdir claude-setup-offline
cd claude-setup-offline

# Download all dependencies
pip download claude-code-setup -d ./packages

# Create installation script
cat > install.sh << 'EOF'
#!/bin/bash
set -e

echo "Installing claude-code-setup in offline environment..."

# Install from local packages
pip install --no-index --find-links ./packages claude-code-setup

echo "Installation complete!"
claude-setup --version
EOF

chmod +x install.sh

# Create archive
cd ..
tar -czf claude-setup-offline.tar.gz claude-setup-offline/

# Transfer to air-gapped system and install
# On target system:
tar -xzf claude-setup-offline.tar.gz
cd claude-setup-offline
./install.sh
```

## Development Deployment

### Hot Reload Development

```bash
# Install in development mode with automatic reloading
pip install -e .

# Use entr for automatic reloading
find src/ -name "*.py" | entr -r python -m claude_code_setup.cli --version

# Or use watchdog
pip install watchdog
watchmedo shell-command --patterns="*.py" --recursive --command='python -m claude_code_setup.cli --version' src/
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: test
        name: Run tests
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

### Health Checks

```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash

echo "=== Claude Setup Health Check ==="

# Check installation
if command -v claude-setup &> /dev/null; then
    echo "✓ claude-setup command available"
else
    echo "✗ claude-setup command not found"
    exit 1
fi

# Check version
VERSION=$(claude-setup --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✓ Version: $VERSION"
else
    echo "✗ Failed to get version"
    exit 1
fi

# Check basic functionality
if claude-setup list --no-interactive &> /dev/null; then
    echo "✓ Basic CLI functionality working"
else
    echo "✗ CLI functionality failed"
    exit 1
fi

# Check configuration
if claude-setup settings show --no-interactive &> /dev/null; then
    echo "✓ Configuration accessible"
else
    echo "ℹ No configuration found (normal for fresh install)"
fi

echo "=== Health Check Complete ==="
EOF

chmod +x health-check.sh
```

This deployment guide covers the complete lifecycle from development to production deployment across various environments and use cases. Choose the appropriate deployment strategy based on your specific requirements and infrastructure.