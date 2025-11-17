#!/usr/bin/env python3
"""
Natural Language Testing Framework

Generates and executes tests from natural language descriptions, analyzes
coverage, and provides interactive testing sessions through voice commands.
"""

import ast
import json
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TestGenerator:
    """Generates test code from natural language descriptions"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def generate_python_test(
        self,
        test_description: str,
        target_file: str,
        target_function: Optional[str] = None,
        test_framework: str = "pytest",
    ) -> Dict:
        """Generate Python test from description"""
        # Read target file to understand context
        target_path = self.project_root / target_file
        if not target_path.exists():
            return {"error": f"Target file not found: {target_file}"}

        try:
            with open(target_path) as f:
                source_code = f.read()
        except Exception as e:
            return {"error": f"Failed to read target file: {str(e)}"}

        # Parse source to extract function signatures
        function_info = self._extract_function_info(source_code, target_function)

        # Generate test code based on description
        test_code = self._create_python_test_code(
            test_description=test_description,
            target_file=target_file,
            function_info=function_info,
            framework=test_framework,
        )

        # Generate test file path
        test_file_path = self._get_test_file_path(target_file, test_framework)

        return {
            "status": "generated",
            "test_code": test_code,
            "test_file_path": str(test_file_path),
            "target_file": target_file,
            "target_function": target_function,
            "framework": test_framework,
        }

    def generate_javascript_test(
        self,
        test_description: str,
        target_file: str,
        target_function: Optional[str] = None,
        test_framework: str = "jest",
    ) -> Dict:
        """Generate JavaScript/TypeScript test from description"""
        target_path = self.project_root / target_file
        if not target_path.exists():
            return {"error": f"Target file not found: {target_file}"}

        try:
            with open(target_path) as f:
                source_code = f.read()
        except Exception as e:
            return {"error": f"Failed to read target file: {str(e)}"}

        # Generate test code
        test_code = self._create_javascript_test_code(
            test_description=test_description,
            target_file=target_file,
            source_code=source_code,
            framework=test_framework,
        )

        # Generate test file path
        test_file_path = self._get_test_file_path(target_file, test_framework)

        return {
            "status": "generated",
            "test_code": test_code,
            "test_file_path": str(test_file_path),
            "target_file": target_file,
            "target_function": target_function,
            "framework": test_framework,
        }

    def _extract_function_info(
        self,
        source_code: str,
        target_function: Optional[str] = None,
    ) -> Dict:
        """Extract function information from Python source"""
        try:
            tree = ast.parse(source_code)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if target_function and node.name != target_function:
                        continue

                    # Extract parameters
                    params = []
                    for arg in node.args.args:
                        params.append(arg.arg)

                    # Extract docstring
                    docstring = ast.get_docstring(node) or ""

                    functions.append({
                        "name": node.name,
                        "params": params,
                        "docstring": docstring,
                        "lineno": node.lineno,
                    })

            return {"functions": functions}

        except Exception as e:
            return {"error": f"Failed to parse source: {str(e)}"}

    def _create_python_test_code(
        self,
        test_description: str,
        target_file: str,
        function_info: Dict,
        framework: str,
    ) -> str:
        """Create Python test code"""
        # Build import statement
        module_path = target_file.replace("/", ".").replace(".py", "")
        imports = f"from {module_path} import *\n"

        if framework == "pytest":
            imports += "import pytest\n"

        # Parse test description to identify test type
        test_type = self._identify_test_type(test_description)

        # Generate test function
        test_name = self._generate_test_name(test_description)
        test_body = self._generate_test_body(
            test_description=test_description,
            function_info=function_info,
            test_type=test_type,
        )

        test_code = f'''"""
Test generated from description:
{test_description}
"""

{imports}

def {test_name}():
    """
    {test_description}
    """
{test_body}
'''

        return test_code

    def _create_javascript_test_code(
        self,
        test_description: str,
        target_file: str,
        source_code: str,
        framework: str,
    ) -> str:
        """Create JavaScript test code"""
        # Extract functions/classes from source
        functions = self._extract_js_functions(source_code)

        # Build import statement
        import_path = target_file.replace(".ts", "").replace(".js", "")
        if functions:
            imports = f"import {{ {', '.join(functions)} }} from './{import_path}';\n"
        else:
            imports = f"import * as module from './{import_path}';\n"

        # Generate test suite
        test_name = self._generate_test_name(test_description)
        test_body = self._generate_js_test_body(
            test_description=test_description,
            functions=functions,
        )

        if framework == "jest":
            test_code = f'''/**
 * Test generated from description:
 * {test_description}
 */

{imports}

describe('{test_name}', () => {{
{test_body}
}});
'''
        else:  # mocha/other
            test_code = f'''/**
 * Test generated from description:
 * {test_description}
 */

{imports}

describe('{test_name}', function() {{
{test_body}
}});
'''

        return test_code

    def _identify_test_type(self, description: str) -> str:
        """Identify test type from description"""
        description_lower = description.lower()

        if any(word in description_lower for word in ["unit", "function", "method"]):
            return "unit"
        elif any(word in description_lower for word in ["integration", "integrate"]):
            return "integration"
        elif any(word in description_lower for word in ["e2e", "end-to-end", "ui", "visual"]):
            return "e2e"
        else:
            return "unit"

    def _generate_test_name(self, description: str) -> str:
        """Generate test function name from description"""
        # Clean description and convert to snake_case
        clean = re.sub(r"[^\w\s]", "", description.lower())
        words = clean.split()[:8]  # Limit to 8 words
        return "test_" + "_".join(words)

    def _generate_test_body(
        self,
        test_description: str,
        function_info: Dict,
        test_type: str,
    ) -> str:
        """Generate test body code"""
        # Basic template - in production, this would use LLM
        functions = function_info.get("functions", [])

        if not functions:
            return '''    # TODO: Implement test
    assert True, "Test not implemented"
'''

        func = functions[0]
        func_name = func["name"]
        params = func["params"]

        # Generate sample test based on description keywords
        body_lines = []
        body_lines.append("    # Arrange")

        # Add parameter setup
        for param in params:
            if param == "self":
                continue
            body_lines.append(f"    {param} = None  # TODO: Set appropriate test value")

        body_lines.append("")
        body_lines.append("    # Act")
        param_list = ", ".join([p for p in params if p != "self"])
        body_lines.append(f"    result = {func_name}({param_list})")

        body_lines.append("")
        body_lines.append("    # Assert")
        if "error" in test_description.lower() or "exception" in test_description.lower():
            body_lines.append("    # TODO: Add exception assertion")
            body_lines.append("    # with pytest.raises(SomeException):")
            body_lines.append("    #     result = " + func_name + "(...)")
        else:
            body_lines.append("    assert result is not None  # TODO: Add specific assertion")

        return "\n".join(body_lines) + "\n"

    def _generate_js_test_body(
        self,
        test_description: str,
        functions: List[str],
    ) -> str:
        """Generate JavaScript test body"""
        if not functions:
            return '''  it('should pass', () => {
    // TODO: Implement test
    expect(true).toBe(true);
  });
'''

        func_name = functions[0]

        body_lines = []
        body_lines.append(f"  it('{test_description}', () => {{")
        body_lines.append("    // Arrange")
        body_lines.append("    const input = null; // TODO: Set appropriate test value")
        body_lines.append("")
        body_lines.append("    // Act")
        body_lines.append(f"    const result = {func_name}(input);")
        body_lines.append("")
        body_lines.append("    // Assert")
        body_lines.append("    expect(result).toBeDefined(); // TODO: Add specific assertion")
        body_lines.append("  });")

        return "\n".join(body_lines) + "\n"

    def _extract_js_functions(self, source_code: str) -> List[str]:
        """Extract function/class names from JavaScript source"""
        # Simple regex-based extraction - in production, use proper parser
        functions = []

        # Match function declarations
        func_pattern = r"(?:export\s+)?(?:function|const|let)\s+(\w+)"
        for match in re.finditer(func_pattern, source_code):
            functions.append(match.group(1))

        # Match class declarations
        class_pattern = r"(?:export\s+)?class\s+(\w+)"
        for match in re.finditer(class_pattern, source_code):
            functions.append(match.group(1))

        return list(set(functions))[:5]  # Limit to 5

    def _get_test_file_path(self, target_file: str, framework: str) -> Path:
        """Generate test file path based on framework conventions"""
        target_path = Path(target_file)

        if framework == "pytest":
            # Python: tests/test_<module>.py
            test_dir = self.project_root / "tests"
            test_file = f"test_{target_path.stem}.py"
            return test_dir / test_file

        elif framework == "jest":
            # JavaScript: <module>.test.js or __tests__/<module>.test.js
            if target_path.suffix == ".ts":
                test_file = f"{target_path.stem}.test.ts"
            else:
                test_file = f"{target_path.stem}.test.js"
            return target_path.parent / "__tests__" / test_file

        else:
            # Generic
            return target_path.parent / f"test_{target_path.name}"


class TestExecutor:
    """Executes tests and analyzes results"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def run_pytest(
        self,
        test_path: Optional[str] = None,
        verbose: bool = True,
        coverage: bool = True,
    ) -> Dict:
        """Run pytest tests"""
        cmd = ["pytest"]

        if test_path:
            cmd.append(str(test_path))

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov", "--cov-report=json"])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            return self._parse_pytest_output(result)

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out after 5 minutes"}
        except Exception as e:
            return {"error": f"Failed to run pytest: {str(e)}"}

    def run_jest(
        self,
        test_path: Optional[str] = None,
        verbose: bool = True,
        coverage: bool = True,
    ) -> Dict:
        """Run Jest tests"""
        cmd = ["npm", "run", "test"]

        if test_path:
            cmd.append(test_path)

        if coverage:
            cmd.append("--coverage")

        if verbose:
            cmd.append("--verbose")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return self._parse_jest_output(result)

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out after 5 minutes"}
        except Exception as e:
            return {"error": f"Failed to run jest: {str(e)}"}

    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse pytest output"""
        output = result.stdout + result.stderr

        # Extract test counts
        passed = len(re.findall(r"PASSED", output))
        failed = len(re.findall(r"FAILED", output))
        skipped = len(re.findall(r"SKIPPED", output))

        # Extract failures
        failures = []
        failure_pattern = r"FAILED\s+([\w/.:]+)\s+-\s+(.+?)(?=\n\n|\Z)"
        for match in re.finditer(failure_pattern, output, re.DOTALL):
            failures.append({
                "test": match.group(1),
                "message": match.group(2).strip(),
            })

        # Load coverage data if available
        coverage_data = None
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            except Exception:
                pass

        return {
            "status": "completed",
            "exit_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "failures": failures,
            "coverage": coverage_data,
            "output": output,
        }

    def _parse_jest_output(self, result: subprocess.CompletedProcess) -> Dict:
        """Parse Jest output"""
        output = result.stdout + result.stderr

        # Extract test counts
        test_suites_match = re.search(r"Test Suites:\s+(\d+)\s+passed.*?(\d+)\s+total", output)
        tests_match = re.search(r"Tests:\s+(\d+)\s+passed.*?(\d+)\s+total", output)

        passed = int(tests_match.group(1)) if tests_match else 0
        total = int(tests_match.group(2)) if tests_match else 0
        failed = total - passed

        # Extract failures
        failures = []
        failure_pattern = r"●\s+(.*?)\n\n\s+(.*?)(?=\n\s+●|\n\nTest Suites:|\Z)"
        for match in re.finditer(failure_pattern, output, re.DOTALL):
            failures.append({
                "test": match.group(1).strip(),
                "message": match.group(2).strip(),
            })

        # Extract coverage summary
        coverage_summary = None
        coverage_match = re.search(
            r"Statements\s+:\s+([\d.]+)%.*?\n.*?Branches\s+:\s+([\d.]+)%.*?\n.*?Functions\s+:\s+([\d.]+)%.*?\n.*?Lines\s+:\s+([\d.]+)%",
            output,
            re.DOTALL,
        )
        if coverage_match:
            coverage_summary = {
                "statements": float(coverage_match.group(1)),
                "branches": float(coverage_match.group(2)),
                "functions": float(coverage_match.group(3)),
                "lines": float(coverage_match.group(4)),
            }

        return {
            "status": "completed",
            "exit_code": result.returncode,
            "passed": passed,
            "failed": failed,
            "total": total,
            "failures": failures,
            "coverage_summary": coverage_summary,
            "output": output,
        }


class CoverageAnalyzer:
    """Analyzes test coverage and identifies gaps"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def analyze_python_coverage(self, coverage_file: str = "coverage.json") -> Dict:
        """Analyze Python coverage from coverage.json"""
        coverage_path = self.project_root / coverage_file

        if not coverage_path.exists():
            return {"error": f"Coverage file not found: {coverage_file}"}

        try:
            with open(coverage_path) as f:
                coverage_data = json.load(f)
        except Exception as e:
            return {"error": f"Failed to parse coverage data: {str(e)}"}

        # Extract file-level coverage
        files = coverage_data.get("files", {})
        file_coverage = []

        for file_path, data in files.items():
            summary = data.get("summary", {})
            file_coverage.append({
                "file": file_path,
                "statements": summary.get("num_statements", 0),
                "missing": summary.get("missing_lines", 0),
                "excluded": summary.get("excluded_lines", 0),
                "coverage": summary.get("percent_covered", 0),
            })

        # Sort by coverage (lowest first)
        file_coverage.sort(key=lambda x: x["coverage"])

        # Calculate overall coverage
        total_statements = sum(f["statements"] for f in file_coverage)
        total_missing = sum(f["missing"] for f in file_coverage)
        overall_coverage = ((total_statements - total_missing) / total_statements * 100) if total_statements > 0 else 0

        # Identify gaps
        gaps = [f for f in file_coverage if f["coverage"] < 80]

        return {
            "overall_coverage": round(overall_coverage, 2),
            "total_statements": total_statements,
            "total_missing": total_missing,
            "file_coverage": file_coverage,
            "coverage_gaps": gaps[:10],  # Top 10 files with lowest coverage
        }

    def suggest_missing_tests(self, coverage_data: Dict) -> List[Dict]:
        """Suggest tests for uncovered code"""
        suggestions = []

        for file_data in coverage_data.get("coverage_gaps", []):
            if file_data["coverage"] < 50:
                priority = "high"
            elif file_data["coverage"] < 80:
                priority = "medium"
            else:
                priority = "low"

            suggestions.append({
                "file": file_data["file"],
                "current_coverage": file_data["coverage"],
                "missing_lines": file_data["missing"],
                "priority": priority,
                "suggestion": f"Add tests to cover {file_data['missing']} missing lines",
            })

        return suggestions


class TestingSession:
    """Manages an interactive testing session"""

    def __init__(self, project_root: str = "."):
        self.session_id = str(uuid.uuid4())
        self.project_root = Path(project_root)
        self.generator = TestGenerator(project_root)
        self.executor = TestExecutor(project_root)
        self.coverage_analyzer = CoverageAnalyzer(project_root)
        self.test_history: List[Dict] = []

    def create_and_run_test(
        self,
        test_description: str,
        target_file: str,
        language: str = "python",
        auto_run: bool = True,
    ) -> Dict:
        """Generate test from description and optionally run it"""
        # Generate test
        if language == "python":
            result = self.generator.generate_python_test(
                test_description=test_description,
                target_file=target_file,
            )
        else:
            result = self.generator.generate_javascript_test(
                test_description=test_description,
                target_file=target_file,
            )

        if "error" in result:
            return result

        # Write test file
        test_file_path = Path(result["test_file_path"])
        test_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(test_file_path, "w") as f:
                f.write(result["test_code"])
        except Exception as e:
            return {"error": f"Failed to write test file: {str(e)}"}

        result["test_file_written"] = str(test_file_path)

        # Run test if requested
        if auto_run:
            if language == "python":
                test_result = self.executor.run_pytest(test_path=str(test_file_path))
            else:
                test_result = self.executor.run_jest(test_path=str(test_file_path))

            result["test_execution"] = test_result

        # Record in history
        self.test_history.append({
            "timestamp": datetime.now().isoformat(),
            "description": test_description,
            "target_file": target_file,
            "test_file": str(test_file_path),
            "result": result,
        })

        return result

    def run_all_tests(self, language: str = "python", coverage: bool = True) -> Dict:
        """Run all tests in the project"""
        if language == "python":
            result = self.executor.run_pytest(coverage=coverage)
        else:
            result = self.executor.run_jest(coverage=coverage)

        # Analyze coverage if available
        if coverage and language == "python":
            coverage_analysis = self.coverage_analyzer.analyze_python_coverage()
            result["coverage_analysis"] = coverage_analysis

            # Get suggestions
            if "coverage_gaps" in coverage_analysis:
                result["test_suggestions"] = self.coverage_analyzer.suggest_missing_tests(
                    coverage_analysis
                )

        return result

    def get_coverage_report(self) -> Dict:
        """Get current coverage report"""
        coverage_data = self.coverage_analyzer.analyze_python_coverage()

        if "error" in coverage_data:
            return coverage_data

        suggestions = self.coverage_analyzer.suggest_missing_tests(coverage_data)

        return {
            "coverage": coverage_data,
            "suggestions": suggestions,
        }

    def get_session_summary(self) -> str:
        """Get testing session summary"""
        total_tests = len(self.test_history)

        summary = f"""
🧪 Testing Session Summary

Session ID: {self.session_id}
Tests Generated: {total_tests}

Recent Tests:
"""

        for i, test in enumerate(self.test_history[-5:], 1):
            summary += f"  {i}. {test['description']}\n"
            summary += f"     Target: {test['target_file']}\n"
            summary += f"     Test File: {test['test_file']}\n"

            if "test_execution" in test.get("result", {}):
                execution = test["result"]["test_execution"]
                summary += f"     Result: {execution.get('passed', 0)} passed, {execution.get('failed', 0)} failed\n"

        return summary
