"""Complexity Analyzer Agent module."""

import ast
from pathlib import Path
from typing import Any, Dict

from claude_code_setup.plugins.agents.types import (
    AgentContext,
    AgentMessage,
    AgentResponse,
    AgentStatus,
)


def calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST node.
    
    Args:
        node: AST node to analyze
        
    Returns:
        Complexity score
    """
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    
    return complexity


async def execute(
    context: AgentContext,
    config: Dict[str, Any],
    stream: bool = False,
    debug: bool = False
) -> AgentResponse:
    """Execute complexity analysis.
    
    Args:
        context: Agent context
        config: Configuration
        stream: Stream responses (not used)
        debug: Debug mode
        
    Returns:
        Agent response
    """
    response = AgentResponse(status=AgentStatus.RUNNING)
    
    # Get configuration
    max_complexity = config.get("max_complexity", 10)
    check_cognitive = config.get("check_cognitive", True)
    
    # Get file to analyze
    file_path = context.current_file
    if not file_path:
        response.status = AgentStatus.FAILED
        response.errors.append("No file specified for analysis")
        return response
    
    try:
        # Read and parse file
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        # Analyze functions and methods
        complex_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = calculate_complexity(node)
                
                if complexity > max_complexity:
                    complex_functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "complexity": complexity,
                        "type": "function"
                    })
        
        # Build response
        if complex_functions:
            report = f"## Complexity Analysis: {Path(file_path).name}\n\n"
            report += f"Found {len(complex_functions)} function(s) exceeding complexity threshold ({max_complexity}):\n\n"
            
            for func in complex_functions:
                report += f"- **{func['name']}** (line {func['line']}): complexity = {func['complexity']}\n"
            
            report += "\n### Recommendations:\n"
            report += "- Consider breaking down complex functions into smaller, focused functions\n"
            report += "- Extract complex conditional logic into separate methods\n"
            report += "- Use early returns to reduce nesting levels\n"
            
            response.messages.append(AgentMessage(
                role="assistant",
                content=report
            ))
        else:
            response.messages.append(AgentMessage(
                role="assistant",
                content=f"✅ All functions have complexity ≤ {max_complexity}. Code complexity looks good!"
            ))
        
        response.results = {
            "file": file_path,
            "max_complexity": max_complexity,
            "complex_functions": complex_functions,
            "total_functions_analyzed": len([
                n for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ])
        }
        
        response.status = AgentStatus.COMPLETED
        
    except SyntaxError as e:
        response.status = AgentStatus.FAILED
        response.errors.append(f"Syntax error in file: {str(e)}")
    except Exception as e:
        response.status = AgentStatus.FAILED
        response.errors.append(f"Analysis failed: {str(e)}")
        if debug:
            import traceback
            response.errors.append(traceback.format_exc())
    
    return response