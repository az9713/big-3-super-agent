#!/usr/bin/env python3
"""
Voice-Activated Debugging Assistant

Analyzes errors, stack traces, and logs to provide intelligent debugging
assistance through voice interaction. Suggests fixes and can interactively
debug code.
"""

import json
import re
import subprocess
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class StackTraceParser:
    """Parse and analyze stack traces"""

    @staticmethod
    def parse_python_traceback(error_text: str) -> Dict:
        """Parse Python traceback into structured format"""
        lines = error_text.strip().split('\n')

        # Extract error type and message
        error_type = ""
        error_message = ""
        if lines:
            last_line = lines[-1]
            if ':' in last_line:
                parts = last_line.split(':', 1)
                error_type = parts[0].strip()
                error_message = parts[1].strip() if len(parts) > 1 else ""
            else:
                error_type = last_line.strip()

        # Extract stack frames
        frames = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('File "'):
                # Parse file, line number, function
                match = re.search(r'File "([^"]+)", line (\d+), in (.+)', line)
                if match:
                    file_path = match.group(1)
                    line_num = int(match.group(2))
                    function = match.group(3)

                    # Get code snippet if available
                    code_snippet = ""
                    if i + 1 < len(lines):
                        code_snippet = lines[i + 1].strip()

                    frames.append({
                        "file": file_path,
                        "line": line_num,
                        "function": function,
                        "code": code_snippet,
                    })
                    i += 2
                    continue
            i += 1

        return {
            "error_type": error_type,
            "error_message": error_message,
            "frames": frames,
            "full_traceback": error_text,
        }

    @staticmethod
    def identify_crash_point(frames: List[Dict]) -> Optional[Dict]:
        """Identify the likely crash point in the stack"""
        if not frames:
            return None

        # Usually the last frame before the error is the crash point
        # But skip standard library frames
        for frame in reversed(frames):
            file_path = frame.get("file", "")
            # Skip site-packages and python lib
            if "site-packages" not in file_path and "/lib/python" not in file_path:
                return frame

        # If all frames are in libraries, return the last one
        return frames[-1] if frames else None


class ErrorAnalyzer:
    """Analyze errors and suggest root causes"""

    # Common error patterns and their likely causes
    ERROR_PATTERNS = {
        "NullPointerException": [
            "Variable is None/null when it shouldn't be",
            "Missing null check before accessing property",
            "API returned null instead of expected object",
            "Uninitialized variable",
        ],
        "AttributeError": [
            "Accessing attribute that doesn't exist on object",
            "Object is None when attribute access attempted",
            "Wrong object type - expected different class",
            "Typo in attribute name",
        ],
        "KeyError": [
            "Dictionary key doesn't exist",
            "Missing required configuration key",
            "Typo in dictionary key name",
            "Data structure changed but code not updated",
        ],
        "IndexError": [
            "List/array index out of bounds",
            "Empty list accessed",
            "Off-by-one error in indexing",
            "Loop bounds incorrect",
        ],
        "TypeError": [
            "Wrong type passed to function",
            "Operation not supported for this type",
            "Missing or extra function arguments",
            "None passed where value expected",
        ],
        "ValueError": [
            "Correct type but invalid value",
            "Value out of expected range",
            "Invalid format for conversion",
            "Unexpected input value",
        ],
        "ConnectionError": [
            "Network connectivity issue",
            "Service not running",
            "Wrong host/port",
            "Firewall blocking connection",
        ],
        "TimeoutError": [
            "Operation took too long",
            "Remote service slow/unresponsive",
            "Timeout configured too short",
            "Resource contention/deadlock",
        ],
    }

    def analyze_error(
        self,
        parsed_trace: Dict,
        context: Optional[Dict] = None,
    ) -> Dict:
        """Analyze error and provide insights"""
        error_type = parsed_trace.get("error_type", "")
        error_message = parsed_trace.get("error_message", "")
        frames = parsed_trace.get("frames", [])

        # Get crash point
        crash_frame = StackTraceParser.identify_crash_point(frames)

        # Get likely causes based on error type
        likely_causes = []
        for pattern, causes in self.ERROR_PATTERNS.items():
            if pattern in error_type:
                likely_causes.extend(causes)

        # Analyze context
        contextual_insights = []
        if crash_frame:
            code = crash_frame.get("code", "")

            # Check for common issues in code
            if code:
                if "None" in code or "null" in code:
                    contextual_insights.append(
                        "Code involves None/null handling - check null checks"
                    )
                if "[" in code and "]" in code:
                    contextual_insights.append(
                        "Array/list indexing present - verify index bounds"
                    )
                if "." in code and "(" in code:
                    contextual_insights.append(
                        "Method call present - verify object is initialized"
                    )

        # Generate suggestions
        suggestions = self._generate_fix_suggestions(
            error_type, error_message, crash_frame, context
        )

        return {
            "error_type": error_type,
            "error_message": error_message,
            "crash_point": crash_frame,
            "likely_causes": likely_causes[:3],  # Top 3 most likely
            "contextual_insights": contextual_insights,
            "suggested_fixes": suggestions,
            "severity": self._assess_severity(error_type),
        }

    def _generate_fix_suggestions(
        self,
        error_type: str,
        error_message: str,
        crash_frame: Optional[Dict],
        context: Optional[Dict],
    ) -> List[str]:
        """Generate specific fix suggestions"""
        suggestions = []

        if "NullPointer" in error_type or "AttributeError" in error_type:
            if crash_frame:
                suggestions.append(
                    f"Add null check before line {crash_frame['line']}: "
                    f"if obj is not None: ..."
                )
                suggestions.append(
                    "Use optional chaining or getattr() with default value"
                )

        if "KeyError" in error_type:
            key = re.search(r"'([^']+)'", error_message)
            if key:
                suggestions.append(
                    f"Use dict.get('{key.group(1)}', default_value) "
                    f"instead of dict['{key.group(1)}']"
                )
            suggestions.append("Check if key exists before accessing: if key in dict")

        if "IndexError" in error_type:
            suggestions.append("Check list length before accessing index")
            suggestions.append("Use enumerate() or range(len(list)) to avoid index errors")

        if "TypeError" in error_type:
            if "argument" in error_message.lower():
                suggestions.append("Check function signature and argument types")
                suggestions.append("Verify correct number of arguments passed")

        if "Connection" in error_type or "Timeout" in error_type:
            suggestions.append("Verify service is running and reachable")
            suggestions.append("Check network connectivity and firewall rules")
            suggestions.append("Add retry logic with exponential backoff")

        return suggestions

    def _assess_severity(self, error_type: str) -> str:
        """Assess error severity"""
        critical_errors = ["SystemExit", "KeyboardInterrupt", "MemoryError"]
        high_errors = ["ConnectionError", "TimeoutError", "ImportError"]

        if any(err in error_type for err in critical_errors):
            return "critical"
        elif any(err in error_type for err in high_errors):
            return "high"
        else:
            return "medium"


class LogAnalyzer:
    """Analyze log files for errors and patterns"""

    def __init__(self):
        self.error_patterns = [
            r"ERROR",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"Failed",
            r"Error:",
        ]

    def analyze_logs(
        self,
        log_path: str,
        recent_lines: int = 100,
    ) -> Dict:
        """Analyze log file for recent errors"""
        try:
            log_file = Path(log_path)
            if not log_file.exists():
                return {"error": f"Log file not found: {log_path}"}

            with open(log_file) as f:
                lines = f.readlines()

            # Get recent lines
            recent = lines[-recent_lines:] if len(lines) > recent_lines else lines

            # Find errors
            errors = []
            warnings = []

            for i, line in enumerate(recent):
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.error_patterns):
                    errors.append({
                        "line_num": len(lines) - recent_lines + i + 1,
                        "content": line.strip(),
                        "timestamp": self._extract_timestamp(line),
                    })
                elif "WARN" in line.upper():
                    warnings.append({
                        "line_num": len(lines) - recent_lines + i + 1,
                        "content": line.strip(),
                        "timestamp": self._extract_timestamp(line),
                    })

            # Group errors by type
            error_groups = self._group_errors(errors)

            return {
                "total_errors": len(errors),
                "total_warnings": len(warnings),
                "recent_errors": errors[-10:],  # Last 10 errors
                "error_groups": error_groups,
                "log_path": log_path,
                "lines_analyzed": len(recent),
            }

        except Exception as e:
            return {"error": f"Failed to analyze logs: {str(e)}"}

    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
            r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}",
            r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)

        return None

    def _group_errors(self, errors: List[Dict]) -> Dict[str, int]:
        """Group errors by type/pattern"""
        groups = defaultdict(int)

        for error in errors:
            content = error["content"]

            # Extract error type
            if "Exception" in content:
                match = re.search(r"(\w+Exception)", content)
                if match:
                    groups[match.group(1)] += 1
            elif "ERROR" in content:
                # Try to extract the error category
                parts = content.split(":")
                if len(parts) > 1:
                    category = parts[0].split()[-1]
                    groups[category] += 1
                else:
                    groups["Generic Error"] += 1
            else:
                groups["Other"] += 1

        return dict(groups)

    def search_logs(
        self,
        log_path: str,
        search_term: str,
        context_lines: int = 2,
    ) -> List[Dict]:
        """Search logs for specific term with context"""
        try:
            with open(log_path) as f:
                lines = f.readlines()

            results = []
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Get context
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)

                    results.append({
                        "line_num": i + 1,
                        "match": line.strip(),
                        "context": [l.strip() for l in lines[start:end]],
                    })

            return results

        except Exception as e:
            return []


class DebuggingSession:
    """Manages an interactive debugging session"""

    def __init__(self):
        self.stack_parser = StackTraceParser()
        self.error_analyzer = ErrorAnalyzer()
        self.log_analyzer = LogAnalyzer()
        self.current_error: Optional[Dict] = None
        self.analysis: Optional[Dict] = None

    def analyze_error(self, error_text: str, context: Optional[Dict] = None) -> Dict:
        """Analyze an error and provide debugging insights"""
        # Parse stack trace
        parsed = self.stack_parser.parse_python_traceback(error_text)

        # Analyze error
        analysis = self.error_analyzer.analyze_error(parsed, context)

        # Store for session
        self.current_error = parsed
        self.analysis = analysis

        return {
            "error_type": analysis["error_type"],
            "error_message": analysis["error_message"],
            "crash_point": analysis["crash_point"],
            "severity": analysis["severity"],
            "likely_causes": analysis["likely_causes"],
            "suggested_fixes": analysis["suggested_fixes"],
            "contextual_insights": analysis["contextual_insights"],
        }

    def analyze_logs(
        self,
        log_path: str,
        search_term: Optional[str] = None,
    ) -> Dict:
        """Analyze logs for errors"""
        if search_term:
            results = self.log_analyzer.search_logs(log_path, search_term)
            return {
                "search_term": search_term,
                "matches": len(results),
                "results": results[:10],  # Limit to 10
            }
        else:
            return self.log_analyzer.analyze_logs(log_path)

    def suggest_breakpoints(self) -> List[Dict]:
        """Suggest where to set breakpoints based on error"""
        if not self.current_error or not self.analysis:
            return []

        suggestions = []
        crash_point = self.analysis.get("crash_point")

        if crash_point:
            # Breakpoint at crash location
            suggestions.append({
                "file": crash_point["file"],
                "line": crash_point["line"],
                "reason": "Crash point - inspect variables here",
            })

            # Breakpoint a few lines before crash
            suggestions.append({
                "file": crash_point["file"],
                "line": max(1, crash_point["line"] - 3),
                "reason": "Before crash - verify assumptions",
            })

        # Add breakpoints at function entry points in stack
        frames = self.current_error.get("frames", [])
        for frame in frames[-3:]:  # Last 3 frames
            # Skip if this is the crash point (avoid duplicates)
            if crash_point and frame["file"] == crash_point.get("file") and frame["line"] == crash_point.get("line"):
                continue
            suggestions.append({
                "file": frame["file"],
                "line": frame["line"],
                "reason": f"In {frame['function']}() - check parameters",
            })

        return suggestions[:5]  # Limit to 5 suggestions

    def generate_fix_code(self) -> Optional[str]:
        """Generate potential fix code"""
        if not self.analysis:
            return None

        error_type = self.analysis.get("error_type", "")
        crash_point = self.analysis.get("crash_point")

        if not crash_point:
            return None

        # Generate fix based on error type
        if "AttributeError" in error_type or "NoneType" in self.analysis.get("error_message", ""):
            return f"""# Fix for {error_type} at line {crash_point['line']}
# Add null check before accessing attribute

if obj is not None:
    # Original code:
    # {crash_point['code']}
    result = obj.attribute
else:
    # Handle None case
    result = default_value  # or raise appropriate error
"""

        elif "KeyError" in error_type:
            key_match = re.search(r"'([^']+)'", self.analysis.get("error_message", ""))
            key = key_match.group(1) if key_match else "key"
            return f"""# Fix for {error_type} at line {crash_point['line']}
# Use dict.get() instead of direct access

# Original code:
# {crash_point['code']}

# Fixed code:
value = dictionary.get('{key}', default_value)
# Or check if key exists:
# if '{key}' in dictionary:
#     value = dictionary['{key}']
"""

        elif "IndexError" in error_type:
            return f"""# Fix for {error_type} at line {crash_point['line']}
# Add bounds check before accessing index

# Original code:
# {crash_point['code']}

# Fixed code:
if 0 <= index < len(list):
    value = list[index]
else:
    # Handle out of bounds
    value = default_value  # or raise appropriate error
"""

        return None

    def get_summary(self) -> str:
        """Get debugging session summary"""
        if not self.analysis:
            return "No error analyzed yet"

        crash_point = self.analysis.get("crash_point", {})

        summary = f"""
🐛 Debugging Summary

Error: {self.analysis['error_type']}
Message: {self.analysis['error_message']}
Severity: {self.analysis['severity'].upper()}

Crash Point:
  File: {crash_point.get('file', 'Unknown')}
  Line: {crash_point.get('line', 'Unknown')}
  Function: {crash_point.get('function', 'Unknown')}
  Code: {crash_point.get('code', 'Unknown')}

Likely Causes:
"""
        for i, cause in enumerate(self.analysis.get('likely_causes', []), 1):
            summary += f"  {i}. {cause}\n"

        summary += "\nSuggested Fixes:\n"
        for i, fix in enumerate(self.analysis.get('suggested_fixes', []), 1):
            summary += f"  {i}. {fix}\n"

        return summary
