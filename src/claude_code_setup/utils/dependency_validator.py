"""Dependency validation for templates and hooks."""

import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set

from ..utils.logger import info, warning, error


class DependencyValidator:
    """Validates dependencies for templates and hooks."""
    
    def __init__(self) -> None:
        """Initialize dependency validator."""
        self._tool_cache: Dict[str, bool] = {}
        self._package_cache: Dict[str, bool] = {}
    
    def validate_template_dependencies(
        self, 
        template_content: str,
        template_name: str,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate dependencies found in template content.
        
        Args:
            template_content: The template content to analyze
            template_name: Name of the template for reporting
            
        Returns:
            Tuple of (all_valid, missing_tools, warnings)
        """
        missing_tools = []
        warnings = []
        
        # Extract tool requirements
        tools = self._extract_tool_requirements(template_content)
        packages = self._extract_package_requirements(template_content)
        
        # Check tools
        for tool in tools:
            if not self._check_tool_available(tool):
                missing_tools.append(tool)
                
        # Check packages (with warnings only)
        for package_type, package_name in packages:
            if not self._check_package_installed(package_type, package_name):
                warnings.append(
                    f"Package '{package_name}' ({package_type}) may need to be installed"
                )
                
        # Check for specific patterns that need tools
        if "npm " in template_content or "npx " in template_content:
            if not self._check_tool_available("npm"):
                missing_tools.append("npm")
                
        if "python " in template_content or "pip " in template_content:
            if not self._check_tool_available("python"):
                missing_tools.append("python")
                
        if "git " in template_content:
            if not self._check_tool_available("git"):
                missing_tools.append("git")
                
        all_valid = len(missing_tools) == 0
        return all_valid, missing_tools, warnings
    
    def _extract_tool_requirements(self, content: str) -> Set[str]:
        """Extract tool requirements from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Set of required tools
        """
        tools = set()
        
        # Common command patterns
        command_patterns = [
            r'\b(npm|npx|node|yarn|pnpm)\s+',
            r'\b(python|python3|pip|pip3)\s+',
            r'\b(git|gh)\s+',
            r'\b(docker|docker-compose)\s+',
            r'\b(make|cmake)\s+',
            r'\b(cargo|rustc)\s+',
            r'\b(go|golang)\s+',
            r'\b(java|javac|mvn|gradle)\s+',
        ]
        
        for pattern in command_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Normalize tool names
                tool = match.lower()
                if tool in ['python3', 'pip3']:
                    tool = tool[:-1]  # Remove '3'
                # If we find pip, also add python as pip requires python
                if tool == 'pip':
                    tools.add('python')
                tools.add(tool)
                
        return tools
    
    def _extract_package_requirements(
        self, 
        content: str
    ) -> List[Tuple[str, str]]:
        """Extract package requirements from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of (package_type, package_name) tuples
        """
        packages = []
        
        # NPM packages
        npm_patterns = [
            r'npm\s+install\s+([a-zA-Z0-9@/\-_]+)',
            r'yarn\s+add\s+([a-zA-Z0-9@/\-_]+)',
            r'pnpm\s+add\s+([a-zA-Z0-9@/\-_]+)',
        ]
        
        for pattern in npm_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                packages.append(('npm', match))
                
        # Python packages
        python_patterns = [
            r'pip\s+install\s+([a-zA-Z0-9\-_\[\]]+)',
            r'import\s+([a-zA-Z0-9_]+)',
            r'from\s+([a-zA-Z0-9_]+)\s+import',
        ]
        
        for pattern in python_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip standard library modules
                if match not in ['os', 'sys', 'json', 'pathlib', 'typing']:
                    packages.append(('python', match))
                    
        return packages
    
    def _check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available on the system.
        
        Args:
            tool: Tool name to check
            
        Returns:
            True if tool is available
        """
        if tool in self._tool_cache:
            return self._tool_cache[tool]
            
        try:
            # Try to run the tool with --version
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            available = result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            available = False
            
        self._tool_cache[tool] = available
        return available
    
    def _check_package_installed(
        self, 
        package_type: str, 
        package_name: str
    ) -> bool:
        """Check if a package is installed.
        
        Args:
            package_type: Type of package (npm, python, etc.)
            package_name: Name of the package
            
        Returns:
            True if package appears to be installed
        """
        cache_key = f"{package_type}:{package_name}"
        if cache_key in self._package_cache:
            return self._package_cache[cache_key]
            
        installed = False
        
        try:
            if package_type == "npm":
                # Check global npm packages
                result = subprocess.run(
                    ["npm", "list", "-g", package_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                installed = result.returncode == 0
                
            elif package_type == "python":
                # Try to import the package
                try:
                    __import__(package_name)
                    installed = True
                except ImportError:
                    # Check with pip
                    result = subprocess.run(
                        ["pip", "show", package_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    installed = result.returncode == 0
                    
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            installed = False
            
        self._package_cache[cache_key] = installed
        return installed
    
    def validate_hook_script(
        self,
        script_path: Path,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate a hook script for dependencies.
        
        Args:
            script_path: Path to the hook script
            
        Returns:
            Tuple of (valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not script_path.exists():
            errors.append(f"Script file not found: {script_path}")
            return False, errors, warnings
            
        # Read script content
        try:
            content = script_path.read_text()
        except Exception as e:
            errors.append(f"Failed to read script: {e}")
            return False, errors, warnings
            
        # Check shebang
        lines = content.splitlines()
        if not lines:
            errors.append("Script is empty")
            return False, errors, warnings
            
        shebang = lines[0]
        if not shebang.startswith("#!"):
            errors.append("Script missing shebang line")
            
        # Validate based on script type
        if script_path.suffix == ".py" or "python" in shebang:
            valid, script_errors, script_warnings = self._validate_python_script(
                content, script_path
            )
            errors.extend(script_errors)
            warnings.extend(script_warnings)
            
        elif script_path.suffix in [".sh", ".bash"] or "bash" in shebang or "sh" in shebang:
            valid, script_errors, script_warnings = self._validate_shell_script(
                content, script_path
            )
            errors.extend(script_errors)
            warnings.extend(script_warnings)
            
        else:
            warnings.append(f"Unknown script type: {script_path.suffix}")
            
        return len(errors) == 0, errors, warnings
    
    def _validate_python_script(
        self,
        content: str,
        script_path: Path,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate a Python script.
        
        Args:
            content: Script content
            script_path: Path to script
            
        Returns:
            Tuple of (valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check syntax
        try:
            compile(content, str(script_path), 'exec')
        except SyntaxError as e:
            errors.append(f"Python syntax error: {e}")
            
        # Check imports
        import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            module = match.group(1) or match.group(2).split(',')[0].strip()
            if not self._check_package_installed('python', module.split('.')[0]):
                warnings.append(f"Python module '{module}' may not be available")
                
        return len(errors) == 0, errors, warnings
    
    def _validate_shell_script(
        self,
        content: str,
        script_path: Path,
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate a shell script.
        
        Args:
            content: Script content
            script_path: Path to script
            
        Returns:
            Tuple of (valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for basic syntax issues
        if content.count('(') != content.count(')'):
            errors.append("Unmatched parentheses in script")
            
        if content.count('[') != content.count(']'):
            errors.append("Unmatched brackets in script")
            
        if content.count('{') != content.count('}'):
            errors.append("Unmatched braces in script")
            
        # Check for required commands
        commands = re.findall(r'\b(\w+)\s*\(', content)  # Functions
        commands.extend(re.findall(r'^\s*(\w+)\s+', content, re.MULTILINE))  # Commands
        
        for cmd in set(commands):
            if cmd not in ['if', 'then', 'else', 'fi', 'for', 'do', 'done', 
                          'while', 'case', 'esac', 'function', 'return', 'exit']:
                if not self._check_tool_available(cmd):
                    warnings.append(f"Command '{cmd}' may not be available")
                    
        return len(errors) == 0, errors, warnings


def create_dependency_validator() -> DependencyValidator:
    """Create a dependency validator instance.
    
    Returns:
        DependencyValidator instance
    """
    return DependencyValidator()