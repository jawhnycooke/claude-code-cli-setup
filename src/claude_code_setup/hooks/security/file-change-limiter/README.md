# File Change Limiter Hook

This hook prevents Claude Code from making too many changes at once, forcing incremental development practices.

## What it does

- Limits the number of files that can be modified in a single operation
- Restricts the size of files being created or edited
- Helps junior developers review and understand changes

## Configuration

The hook can be configured using environment variables:

- `MAX_FILES_PER_OPERATION`: Maximum files per operation (default: 3)
- `MAX_LINES_PER_FILE`: Maximum lines per file (default: 100)

## Usage

When this hook is active, Claude Code will be blocked from:
- Modifying more than 3 files at once
- Creating or editing files larger than 100 lines

This encourages:
- Smaller, focused changes
- Easier code review
- Better understanding of modifications

## Example

```bash
# Set custom limits
export MAX_FILES_PER_OPERATION=5
export MAX_LINES_PER_FILE=200
```