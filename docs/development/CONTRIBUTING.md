# Contributing to Claude Code Setup

We love your input! We want to make contributing to Claude Code Setup as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Submit that pull request!

### Coding Style

* TypeScript style using ESLint and Prettier
* 2 spaces for indentation rather than tabs
* Semi-colons at the end of lines
* Single quotes for strings
* Prefer `const` over `let` when possible
* Use modern ES6+ features
* Explicit types for function arguments and return values

## Adding New Command Templates

If you want to add new command templates:

1. Add the template definition to `src/utils/template.ts`
2. Make sure to provide:
   - A clear template name
   - A descriptive category
   - Well-formatted template content
   - Clear instructions for the $ARGUMENTS parameter (if any)
3. Update the README to mention the new template

Example template definition:

```typescript
'new-template': {
  name: 'new-template',
  description: 'New Template Description',
  category: 'category',
  content: `# Template Title

This is a template with a parameter:
$ARGUMENTS

More content here...`
}
```

## Release Process

We use GitHub Actions to automatically publish new versions to npm. The process is:

1. Code changes are merged to main
2. A maintainer triggers the "Create Version Tag" workflow, specifying the version bump type (patch, minor, major)
3. This creates a new git tag (e.g., v0.1.1)
4. The tag creation triggers the "Create Release" and "Update Version" workflows
5. A GitHub release is created with auto-generated notes
6. The package is published to npm

### Version Guidelines

- **Patch (0.0.X)** - Bug fixes and minor changes
- **Minor (0.X.0)** - New features, backward compatible
- **Major (X.0.0)** - Breaking changes

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.