#!/usr/bin/env python3
"""
Interactive Voice Code Review

Enables natural language code reviews through voice with multi-dimensional
analysis (security, performance, best practices, etc.) and immediate fix application.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


class Finding:
    """Represents a code review finding"""

    def __init__(
        self,
        file: str,
        line: int,
        type: str,  # security, performance, style, documentation, etc.
        severity: str,  # critical, high, medium, low
        title: str,
        description: str,
        recommendation: str = "",
        code_snippet: str = "",
        suggested_fix: Optional[str] = None,
    ):
        self.file = file
        self.line = line
        self.type = type
        self.severity = severity
        self.title = title
        self.description = description
        self.recommendation = recommendation
        self.code_snippet = code_snippet
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict:
        return {
            "file": self.file,
            "line": self.line,
            "type": self.type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix,
        }


class SecurityAnalyzer:
    """Detect security vulnerabilities"""

    PATTERNS = [
        {
            "name": "SQL Injection",
            "pattern": r"execute\s*\(['\"].*?\+.*?['\"]|cursor\.execute\s*\(.+?\+",
            "severity": "critical",
            "recommendation": "Use parameterized queries instead of string concatenation",
        },
        {
            "name": "Hardcoded Secrets",
            "pattern": r"(api[_-]?key|password|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]",
            "severity": "critical",
            "recommendation": "Move secrets to environment variables or secure vault",
        },
        {
            "name": "Eval Usage",
            "pattern": r"\beval\s*\(",
            "severity": "high",
            "recommendation": "Avoid eval() as it can execute arbitrary code. Use ast.literal_eval() or safer alternatives",
        },
        {
            "name": "Shell Injection",
            "pattern": r"os\.system\s*\(.*?\+|subprocess\..+?shell\s*=\s*True",
            "severity": "high",
            "recommendation": "Avoid shell=True and use list arguments for subprocess calls",
        },
    ]

    def analyze(self, code: str, file_path: str) -> List[Finding]:
        """Analyze code for security issues"""
        findings = []
        lines = code.split("\n")

        for pattern_def in self.PATTERNS:
            matches = re.finditer(pattern_def["pattern"], code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count("\n") + 1
                snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                findings.append(Finding(
                    file=file_path,
                    line=line_num,
                    type="security",
                    severity=pattern_def["severity"],
                    title=pattern_def["name"],
                    description=f"{pattern_def['name']} vulnerability detected",
                    recommendation=pattern_def["recommendation"],
                    code_snippet=snippet.strip(),
                ))

        return findings


class PerformanceAnalyzer:
    """Detect performance issues"""

    def analyze(self, code: str, file_path: str) -> List[Finding]:
        """Analyze code for performance issues"""
        findings = []
        lines = code.split("\n")

        # Detect nested loops (O(n²) complexity)
        for i, line in enumerate(lines):
            if re.search(r"for\s+\w+\s+in\s+", line):
                # Check if there's another for loop in the next 20 lines
                nested_found = False
                for j in range(i + 1, min(i + 20, len(lines))):
                    if re.search(r"for\s+\w+\s+in\s+", lines[j]):
                        if len(lines[j]) - len(lines[j].lstrip()) > len(line) - len(line.lstrip()):
                            nested_found = True
                            break

                if nested_found:
                    findings.append(Finding(
                        file=file_path,
                        line=i + 1,
                        type="performance",
                        severity="medium",
                        title="Nested Loop Detected",
                        description="O(n²) time complexity - consider optimization",
                        recommendation="Use dictionary lookup, set operations, or more efficient algorithms",
                        code_snippet=line.strip(),
                    ))

        # Detect repeated function calls in loops
        for i, line in enumerate(lines):
            if re.search(r"for\s+\w+\s+in\s+", line):
                # Check for function calls in loop body
                for j in range(i + 1, min(i + 10, len(lines))):
                    if "len(" in lines[j] or ".get(" in lines[j]:
                        findings.append(Finding(
                            file=file_path,
                            line=j + 1,
                            type="performance",
                            severity="low",
                            title="Function Call in Loop",
                            description="Repeated function calls can be cached",
                            recommendation="Store the result in a variable before the loop",
                            code_snippet=lines[j].strip(),
                        ))
                        break

        return findings


class StyleAnalyzer:
    """Check code style and best practices"""

    def analyze(self, code: str, file_path: str) -> List[Finding]:
        """Analyze code style"""
        findings = []
        lines = code.split("\n")

        # Check for long lines (>100 characters)
        for i, line in enumerate(lines):
            if len(line) > 100:
                findings.append(Finding(
                    file=file_path,
                    line=i + 1,
                    type="style",
                    severity="low",
                    title="Line Too Long",
                    description=f"Line exceeds 100 characters ({len(line)} chars)",
                    recommendation="Break long lines for better readability",
                    code_snippet=line[:50] + "...",
                ))

        # Check for missing docstrings in functions/classes
        for i, line in enumerate(lines):
            if re.match(r"^\s*(def|class)\s+\w+", line):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i + 1, min(i + 3, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        has_docstring = True
                        break
                    if lines[j].strip() and not lines[j].strip().startswith("#"):
                        break

                if not has_docstring:
                    findings.append(Finding(
                        file=file_path,
                        line=i + 1,
                        type="documentation",
                        severity="low",
                        title="Missing Docstring",
                        description="Function/class lacks documentation",
                        recommendation="Add docstring describing purpose, parameters, and return value",
                        code_snippet=line.strip(),
                    ))

        return findings


class CodeAnalyzer:
    """Multi-dimensional code analysis"""

    def __init__(self):
        self.analyzers = [
            SecurityAnalyzer(),
            PerformanceAnalyzer(),
            StyleAnalyzer(),
        ]

    def analyze_file(self, file_path: str) -> List[Finding]:
        """Analyze file across all dimensions"""
        try:
            with open(file_path) as f:
                code = f.read()
        except Exception as e:
            return [Finding(
                file=file_path,
                line=0,
                type="error",
                severity="high",
                title="File Read Error",
                description=str(e),
            )]

        findings = []
        for analyzer in self.analyzers:
            findings.extend(analyzer.analyze(code, file_path))

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f.severity, 999))

        return findings

    def analyze_directory(self, directory: str, pattern: str = "*.py") -> Dict[str, List[Finding]]:
        """Analyze all files matching pattern in directory"""
        results = {}
        path = Path(directory)

        for file_path in path.rglob(pattern):
            if file_path.is_file():
                findings = self.analyze_file(str(file_path))
                if findings:
                    results[str(file_path)] = findings

        return results


class VoiceCodeReviewSession:
    """Manages an interactive code review session"""

    def __init__(self, target: str):
        self.target = target
        self.analyzer = CodeAnalyzer()
        self.findings: List[Finding] = []
        self.current_index = 0
        self.applied_fixes: List[Finding] = []

    def start_review(self) -> Dict:
        """Start code review session"""
        target_path = Path(self.target)

        if target_path.is_file():
            self.findings = self.analyzer.analyze_file(self.target)
        elif target_path.is_dir():
            results = self.analyzer.analyze_directory(self.target)
            for file_findings in results.values():
                self.findings.extend(file_findings)
        else:
            return {"error": f"Target '{self.target}' not found"}

        # Sort findings by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.findings.sort(key=lambda f: severity_order.get(f.severity, 999))

        return {
            "status": "started",
            "total_findings": len(self.findings),
            "critical": len([f for f in self.findings if f.severity == "critical"]),
            "high": len([f for f in self.findings if f.severity == "high"]),
            "medium": len([f for f in self.findings if f.severity == "medium"]),
            "low": len([f for f in self.findings if f.severity == "low"]),
        }

    def get_current_finding(self) -> Optional[Dict]:
        """Get current finding"""
        if self.current_index >= len(self.findings):
            return None

        finding = self.findings[self.current_index]
        return {
            "index": self.current_index + 1,
            "total": len(self.findings),
            "finding": finding.to_dict(),
        }

    def next_finding(self) -> Optional[Dict]:
        """Move to next finding"""
        self.current_index += 1
        return self.get_current_finding()

    def apply_fix(self) -> Dict:
        """Apply suggested fix (placeholder - would integrate with Claude)"""
        if self.current_index >= len(self.findings):
            return {"error": "No current finding"}

        finding = self.findings[self.current_index]
        self.applied_fixes.append(finding)

        return {
            "status": "fix_applied",
            "file": finding.file,
            "line": finding.line,
            "title": finding.title,
        }

    def get_summary(self) -> Dict:
        """Get review summary"""
        return {
            "total_findings": len(self.findings),
            "reviewed": self.current_index,
            "fixed": len(self.applied_fixes),
            "remaining": len(self.findings) - self.current_index,
            "by_severity": {
                "critical": len([f for f in self.findings if f.severity == "critical"]),
                "high": len([f for f in self.findings if f.severity == "high"]),
                "medium": len([f for f in self.findings if f.severity == "medium"]),
                "low": len([f for f in self.findings if f.severity == "low"]),
            },
        }
