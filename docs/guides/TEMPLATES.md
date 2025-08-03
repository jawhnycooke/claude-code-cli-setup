# Claude Code Setup - Template Reference

This document provides a comprehensive overview of all available templates in Claude Code Setup, helping users quickly understand what each template does and when to use them.

## Overview

Claude Code Setup includes 7 specialized command templates organized into 4 categories. Each template is designed to solve specific development challenges and can be easily installed using the `claude-setup add template` command.

## Template Categories

### General Purpose Templates

These templates provide essential development workflows that apply across multiple programming languages and project types.

#### code-review
**Purpose**: Comprehensive code review using specialized AI subagents

**What it does**: This template implements an advanced code review system that creates five specialized AI subagents to analyze different aspects of your Python code simultaneously. Each subagent focuses on a specific area: style compliance (PEP 8), type hint verification, documentation quality, security vulnerabilities, and performance optimization.

**When to use**: 
- Before merging pull requests
- When refactoring existing code
- During code quality audits
- When preparing code for production deployment

**Key features**:
- Parallel analysis using multiple specialized subagents
- Comprehensive coverage of style, types, documentation, security, and performance
- Actionable recommendations prioritized by importance
- Code examples showing both issues and suggested improvements

**Installation**: `claude-setup add template code-review`

#### fix-issue
**Purpose**: Systematically analyze and fix GitHub issues using parallel AI subagents

**What it does**: This template creates four specialized subagents that work together to understand, implement, test, and review solutions for GitHub issues. The Analysis Subagent investigates the issue, the Implementation Subagent drafts solutions, the Testing Subagent creates verification tests, and the Review Subagent checks for side effects.

**When to use**:
- When addressing GitHub issues in your repository
- For systematic bug fixing workflows
- When you need comprehensive analysis before implementing changes
- To ensure thorough testing of issue fixes

**Key features**:
- Automated GitHub issue analysis using `gh issue view`
- Multiple solution approaches with tradeoff evaluation
- Comprehensive test case creation including edge cases
- Side effect and compatibility verification

**Installation**: `claude-setup add template fix-issue`

### Python Development Templates

Templates specifically designed for Python development workflows and optimization.

#### python-optimization
**Purpose**: Analyze Python code for performance bottlenecks and optimization opportunities

**What it does**: This template provides systematic analysis of Python code focusing on six critical performance areas: algorithmic complexity, memory usage, I/O operations, CPU-bound optimizations, parallelization opportunities, and caching strategies.

**When to use**:
- When your Python application has performance issues
- Before deploying to production environments
- During performance optimization sprints
- When scaling applications to handle larger datasets

**Key features**:
- Algorithmic complexity analysis with Big O assessments
- Memory usage profiling and optimization suggestions
- I/O operation efficiency evaluation
- CPU-bound optimization recommendations
- Parallelization opportunity identification
- Caching strategy implementation guidance

**Installation**: `claude-setup add template python-optimization`

### Node.js Development Templates

Templates for JavaScript and TypeScript development optimization.

#### node-optimization
**Purpose**: Analyze JavaScript/TypeScript code for performance improvements

**What it does**: This template focuses on Node.js-specific performance optimization, analyzing algorithmic complexity, memory usage, asynchronous operations, event loop optimization, network/I/O efficiency, and caching techniques specifically for JavaScript environments.

**When to use**:
- When optimizing Node.js applications
- For frontend performance improvements
- When dealing with event loop blocking issues
- For API performance optimization

**Key features**:
- Asynchronous operation optimization
- Event loop performance analysis
- Network and I/O efficiency improvements
- Memory leak detection and prevention
- Caching and memoization strategies

**Installation**: `claude-setup add template node-optimization`

### Project Management Templates

Templates designed to help with project planning, documentation, and task management.

#### create-tasks
**Purpose**: Break down project goals into comprehensive, manageable task lists

**What it does**: This template uses four parallel subagents to analyze different aspects of a project goal: Architecture Subagent (component identification), Implementation Subagent (technical details), Planning Subagent (timeline and dependencies), and Risk Subagent (challenges and mitigations). The output is a structured TASKS.md file with detailed task tracking.

**When to use**:
- At the start of new projects or features
- When planning complex implementations
- For project estimation and timeline creation
- When breaking down large initiatives into actionable items

**Key features**:
- Multi-dimensional project analysis using specialized subagents
- Structured TASKS.md file generation with progress tracking
- Task dependency mapping and timeline estimation
- Risk identification and mitigation planning
- Status indicators for progress tracking

**Installation**: `claude-setup add template create-tasks`

#### update-tasks
**Purpose**: Verify and update task status in existing TASKS.md files

**What it does**: This template analyzes your codebase to determine the actual completion status of tasks in your TASKS.md file. It uses verification subagents to provide evidence for status changes and automatically updates progress indicators and completion percentages.

**When to use**:
- During regular project status updates
- Before project meetings or reviews
- When tracking milestone completion
- For accurate project progress reporting

**Key features**:
- Automated codebase analysis for task verification
- Evidence-based status updates
- Progress percentage recalculation
- Integration of new tasks discovered during implementation
- Summary of completed work and remaining tasks

**Installation**: `claude-setup add template update-tasks`

#### generate-docs
**Purpose**: Create comprehensive project documentation by analyzing existing code

**What it does**: This template analyzes your codebase to generate factual, comprehensive documentation including README.md, ARCHITECTURE.md, SETUP.md, and USAGE.md. It focuses on documenting what actually exists in the code rather than speculating about future features.

**When to use**:
- When starting documentation for existing projects
- For creating onboarding materials for new team members
- When preparing project handoffs
- For open-source project documentation

**Key features**:
- Automated codebase analysis for accurate documentation
- Multiple document types (README, ARCHITECTURE, SETUP, USAGE)
- Mermaid diagrams for architecture visualization
- Factual, paragraph-style writing without speculation
- Code examples demonstrating actual functionality

**Installation**: `claude-setup add template generate-docs`

## Installation and Usage

### Installing Templates

You can install templates individually or through the interactive interface:

```bash
# Install specific template
claude-setup add template python-optimization

# Install from specific category
claude-setup add template --category python

# Interactive selection
claude-setup add template
```

### Using Templates

Once installed, templates appear as slash commands in Claude Code:

```bash
# In Claude Code
/python-optimization [code to analyze]
/code-review [files to review]
/fix-issue [issue number]
/create-tasks [project goal description]
```

### Template Customization

Templates support argument substitution using `$ARGUMENTS`:
- Single argument: The template receives your input directly
- Multiple arguments: Provide space-separated values
- Complex inputs: Use quotes for multi-word arguments

## Choosing the Right Template

### For Code Quality
- **code-review**: Comprehensive analysis with multiple specialized perspectives
- **python-optimization**: Performance-focused analysis for Python code
- **node-optimization**: Performance-focused analysis for JavaScript/TypeScript

### For Project Management
- **create-tasks**: Breaking down new projects or features into manageable tasks
- **update-tasks**: Maintaining accurate project status and progress tracking
- **generate-docs**: Creating comprehensive documentation for existing projects

### For Issue Resolution
- **fix-issue**: Systematic approach to GitHub issue resolution with comprehensive testing

## Template Performance and Features

All templates are designed to:
- Execute quickly using optimized Python implementations
- Provide detailed, actionable output
- Support both interactive and non-interactive usage
- Integrate seamlessly with existing development workflows
- Generate output that can be directly used in your development process

## Getting Help

For more information about specific templates:
- Use `claude-setup list templates` to see all available templates
- Check the template files directly in `.claude/commands/` after installation
- Refer to the [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete command documentation
- Visit the project repository for additional examples and community templates

## Contributing Templates

Templates are Markdown files with special argument substitution. To create custom templates:
1. Create a `.md` file with your template content
2. Use `$ARGUMENTS` for parameter substitution
3. Place in the appropriate category directory
4. Test with the `claude-setup` command

The template system supports any workflow that can be expressed as instructions to Claude Code, making it highly extensible for team-specific needs.