import os
import re
import ast
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import gitlab_client


class CodeAnalyzer:
    def __init__(self):
        self.language_parsers = {
            'python': self._analyze_python,
            'javascript': self._analyze_javascript,
            'typescript': self._analyze_typescript,
            'react': self._analyze_react,
            'java': self._analyze_java,
            'go': self._analyze_go
        }
        
    async def analyze_repository(self, repo_id: str, repo_path: str = None) -> Dict[str, Any]:
        """Analyze repository structure and code"""
        try:
            # Get repository files
            files = await gitlab_client.list_files(repo_id)
            
            analysis_result = {
                "repository_id": repo_id,
                "services": [],
                "components": [],
                "dependencies": [],
                "api_endpoints": [],
                "database_models": [],
                "configuration": {}
            }
            
            # Analyze each file
            for file_info in files:
                if file_info.get("type") == "file":
                    file_path = file_info.get("path", "")
                    content = await gitlab_client.get_file_content(repo_id, file_path)
                    
                    if content:
                        file_analysis = self.analyze_file(file_path, content)
                        if file_analysis:
                            self._merge_analysis(analysis_result, file_analysis)
            
            return analysis_result
            
        except Exception as e:
            print(f"Error analyzing repository {repo_id}: {e}")
            return {}
    
    def analyze_file(self, file_path: str, content: str) -> Optional[Dict[str, Any]]:
        """Analyze single file"""
        file_ext = Path(file_path).suffix.lower()
        language = self._detect_language(file_path, file_ext)
        
        if language in self.language_parsers:
            return self.language_parsers[language](file_path, content)
        
        return None
    
    def _detect_language(self, file_path: str, file_ext: str) -> str:
        """Detect programming language from file"""
        if file_ext == '.py':
            return 'python'
        elif file_ext in ['.js', '.jsx']:
            return 'javascript'
        elif file_ext in ['.ts', '.tsx']:
            return 'typescript'
        elif file_ext == '.java':
            return 'java'
        elif file_ext == '.go':
            return 'go'
        elif 'package.json' in file_path:
            return 'javascript'
        elif 'requirements.txt' in file_path:
            return 'python'
        else:
            return 'unknown'
    
    def _analyze_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Python file"""
        try:
            tree = ast.parse(content)
            analysis = {
                "classes": [],
                "functions": [],
                "imports": [],
                "api_endpoints": [],
                "database_models": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [],
                        "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    }
                    
                    # Check for database models
                    if any(base in ['Model', 'Base'] for base in class_info["bases"]):
                        analysis["database_models"].append(class_info)
                    
                    # Check for API classes
                    if any('api' in dec.lower() or 'route' in dec.lower() for dec in class_info["decorators"]):
                        analysis["api_endpoints"].append(class_info)
                    
                    analysis["classes"].append(class_info)
                    
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    }
                    
                    # Check for API endpoints
                    if any('route' in dec.lower() or 'endpoint' in dec.lower() for dec in func_info["decorators"]):
                        analysis["api_endpoints"].append(func_info)
                    
                    analysis["functions"].append(func_info)
                    
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
            
            return analysis
            
        except SyntaxError:
            return {}
    
    def _analyze_javascript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze JavaScript file"""
        analysis = {
            "classes": [],
            "functions": [],
            "imports": [],
            "api_endpoints": [],
            "components": []
        }
        
        # Extract imports
        import_pattern = r'import\s+(?:\{[^}]*\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        analysis["imports"].extend(imports)
        
        # Extract classes
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        classes = re.finditer(class_pattern, content)
        for match in classes:
            class_info = {
                "name": match.group(1),
                "extends": match.group(2),
                "line": content[:match.start()].count('\n') + 1
            }
            analysis["classes"].append(class_info)
        
        # Extract functions
        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
        functions = re.finditer(func_pattern, content)
        for match in functions:
            func_name = match.group(1) or match.group(2)
            if func_name:
                func_info = {
                    "name": func_name,
                    "line": content[:match.start()].count('\n') + 1
                }
                analysis["functions"].append(func_info)
        
        # Check for React components
        if 'React' in content or 'react' in file_path.lower():
            component_pattern = r'(?:export\s+)?(?:default\s+)?(?:function|const)\s+(\w+)(?:\s*\([^)]*\)\s*{|.*=.*\([^)]*\)\s*=>)'
            components = re.finditer(component_pattern, content)
            for match in components:
                component_info = {
                    "name": match.group(1),
                    "line": content[:match.start()].count('\n') + 1
                }
                analysis["components"].append(component_info)
        
        return analysis
    
    def _analyze_typescript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze TypeScript file"""
        # Similar to JavaScript but with type annotations
        return self._analyze_javascript(file_path, content)
    
    def _analyze_react(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze React file specifically"""
        analysis = self._analyze_javascript(file_path, content)
        
        # Additional React-specific analysis
        # Extract JSX components
        jsx_pattern = r'<(\w+)(?:\s+[^>]*)?>'
        jsx_components = set(re.findall(jsx_pattern, content))
        analysis["jsx_components"] = list(jsx_components)
        
        # Extract hooks usage
        hook_pattern = r'use[A-Z]\w+'
        hooks = re.findall(hook_pattern, content)
        analysis["hooks"] = list(set(hooks))
        
        return analysis
    
    def _analyze_java(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Java file"""
        analysis = {
            "classes": [],
            "methods": [],
            "imports": [],
            "api_endpoints": []
        }
        
        # Extract imports
        import_pattern = r'import\s+([^;]+);'
        imports = re.findall(import_pattern, content)
        analysis["imports"].extend(imports)
        
        # Extract classes
        class_pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        classes = re.finditer(class_pattern, content)
        for match in classes:
            class_info = {
                "name": match.group(1),
                "extends": match.group(2),
                "implements": match.group(3).split(',') if match.group(3) else [],
                "line": content[:match.start()].count('\n') + 1
            }
            analysis["classes"].append(class_info)
        
        # Extract methods
        method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?(?:final\s+)?(?:<[^>]+>\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
        methods = re.finditer(method_pattern, content)
        for match in methods:
            method_info = {
                "return_type": match.group(1),
                "name": match.group(2),
                "line": content[:match.start()].count('\n') + 1
            }
            analysis["methods"].append(method_info)
        
        return analysis
    
    def _analyze_go(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Go file"""
        analysis = {
            "structs": [],
            "functions": [],
            "imports": [],
            "api_endpoints": []
        }
        
        # Extract imports
        import_pattern = r'import\s+\(([^)]+)\)'
        import_blocks = re.findall(import_pattern, content)
        for block in import_blocks:
            imports = re.findall(r'[\'"]([^\'"]+)[\'"]', block)
            analysis["imports"].extend(imports)
        
        # Extract structs
        struct_pattern = r'type\s+(\w+)\s+struct'
        structs = re.finditer(struct_pattern, content)
        for match in structs:
            struct_info = {
                "name": match.group(1),
                "line": content[:match.start()].count('\n') + 1
            }
            analysis["structs"].append(struct_info)
        
        # Extract functions
        func_pattern = r'func\s+(?:\(\w+\s+\w+\)\s+)?(\w+)\s*\([^)]*\)'
        functions = re.finditer(func_pattern, content)
        for match in functions:
            func_info = {
                "name": match.group(1),
                "line": content[:match.start()].count('\n') + 1
            }
            analysis["functions"].append(func_info)
        
        return analysis
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return ""
    
    def _merge_analysis(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Merge analysis results"""
        for key, value in source.items():
            if key in target and isinstance(target[key], list) and isinstance(value, list):
                target[key].extend(value)
            elif key not in target:
                target[key] = value
    
    def extract_service_info(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract service information from analysis"""
        services = []
        
        # Look for service indicators
        service_indicators = [
            'service', 'api', 'controller', 'handler', 'endpoint',
            'server', 'app', 'main', 'application'
        ]
        
        for class_info in analysis_result.get("classes", []):
            class_name = class_info.get("name", "").lower()
            if any(indicator in class_name for indicator in service_indicators):
                services.append({
                    "name": class_info.get("name"),
                    "type": "service",
                    "methods": class_info.get("methods", []),
                    "line": class_info.get("line")
                })
        
        return services
    
    def extract_api_endpoints(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract API endpoints from analysis"""
        endpoints = []
        
        # Python Flask/FastAPI endpoints
        for func_info in analysis_result.get("functions", []):
            decorators = func_info.get("decorators", [])
            if any('route' in dec.lower() or 'endpoint' in dec.lower() for dec in decorators):
                endpoints.append({
                    "name": func_info.get("name"),
                    "type": "endpoint",
                    "decorators": decorators,
                    "line": func_info.get("line")
                })
        
        # React components that might be pages
        for component_info in analysis_result.get("components", []):
            component_name = component_info.get("name", "").lower()
            if any(page in component_name for page in ['page', 'screen', 'view']):
                endpoints.append({
                    "name": component_info.get("name"),
                    "type": "page",
                    "line": component_info.get("line")
                })
        
        return endpoints
    
    def find_code_references(self, analysis_result: Dict[str, Any], search_term: str) -> List[Dict[str, Any]]:
        """Find code references matching search term"""
        references = []
        search_term_lower = search_term.lower()
        
        # Search in classes
        for class_info in analysis_result.get("classes", []):
            if search_term_lower in class_info.get("name", "").lower():
                references.append({
                    "type": "class",
                    "name": class_info.get("name"),
                    "line": class_info.get("line"),
                    "file": analysis_result.get("file_path", "")
                })
        
        # Search in functions
        for func_info in analysis_result.get("functions", []):
            if search_term_lower in func_info.get("name", "").lower():
                references.append({
                    "type": "function",
                    "name": func_info.get("name"),
                    "line": func_info.get("line"),
                    "file": analysis_result.get("file_path", "")
                })
        
        # Search in components
        for component_info in analysis_result.get("components", []):
            if search_term_lower in component_info.get("name", "").lower():
                references.append({
                    "type": "component",
                    "name": component_info.get("name"),
                    "line": component_info.get("line"),
                    "file": analysis_result.get("file_path", "")
                })
        
        return references