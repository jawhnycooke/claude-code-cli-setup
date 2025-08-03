#!/usr/bin/env python3
"""Code Review Agent implementation."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def analyze_code(file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze code and generate review.
    
    Args:
        file_path: Path to file to review
        config: Agent configuration
        
    Returns:
        Review results
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        return {
            "error": f"Failed to read file: {str(e)}"
        }
    
    # Simple example analysis
    lines = content.split('\n')
    issues = []
    suggestions = []
    
    # Check for basic issues
    for i, line in enumerate(lines, 1):
        # Long lines
        if len(line) > 88:
            issues.append({
                "line": i,
                "severity": "warning",
                "message": f"Line too long ({len(line)} > 88 characters)",
                "category": "style"
            })
        
        # TODO comments
        if "TODO" in line or "FIXME" in line:
            issues.append({
                "line": i,
                "severity": "info",
                "message": "Found TODO/FIXME comment",
                "category": "maintenance"
            })
        
        # Basic security checks
        if "eval(" in line or "exec(" in line:
            issues.append({
                "line": i,
                "severity": "error",
                "message": "Potentially unsafe use of eval/exec",
                "category": "security"
            })
    
    # Generate suggestions
    if len(lines) > 500:
        suggestions.append({
            "type": "refactor",
            "message": "Consider breaking this file into smaller modules"
        })
    
    return {
        "file": file_path,
        "line_count": len(lines),
        "issues": issues,
        "suggestions": suggestions,
        "summary": {
            "total_issues": len(issues),
            "errors": len([i for i in issues if i["severity"] == "error"]),
            "warnings": len([i for i in issues if i["severity"] == "warning"]),
            "info": len([i for i in issues if i["severity"] == "info"])
        }
    }


def main():
    """Main entry point for agent script."""
    # Read input
    try:
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        response = {
            "status": "failed",
            "errors": [f"Failed to parse input: {str(e)}"]
        }
        print(json.dumps(response))
        return 1
    
    context = input_data.get("context", {})
    config = input_data.get("config", {})
    
    # Get file to review
    file_path = context.get("current_file")
    if not file_path:
        response = {
            "status": "failed",
            "errors": ["No file specified for review"]
        }
        print(json.dumps(response))
        return 1
    
    # Perform analysis
    results = analyze_code(file_path, config)
    
    # Build response
    messages = []
    
    if "error" in results:
        response = {
            "status": "failed",
            "errors": [results["error"]]
        }
    else:
        # Format review message
        review_text = f"## Code Review: {Path(file_path).name}\n\n"
        review_text += f"**Lines:** {results['line_count']}\n"
        review_text += f"**Issues:** {results['summary']['total_issues']}\n"
        
        if results['issues']:
            review_text += "\n### Issues Found:\n"
            for issue in results['issues']:
                review_text += f"- Line {issue['line']} [{issue['severity']}]: {issue['message']}\n"
        
        if results['suggestions']:
            review_text += "\n### Suggestions:\n"
            for suggestion in results['suggestions']:
                review_text += f"- {suggestion['message']}\n"
        
        messages.append({
            "role": "assistant",
            "content": review_text
        })
        
        response = {
            "status": "completed",
            "messages": messages,
            "results": results
        }
    
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())