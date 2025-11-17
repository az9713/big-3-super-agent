#!/usr/bin/env python3
"""
Voice Command Macros & Workflow Templates

Enables users to define and execute complex multi-step workflows with a single
voice command, including conditional logic, loops, and error handling.
"""

import json
import re
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class MacroParameter:
    """Represents a macro parameter"""

    def __init__(
        self,
        name: str,
        type: str = "string",
        description: str = "",
        required: bool = False,
        default: Any = None,
        validation: Optional[Dict] = None,
    ):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.default = default
        self.validation = validation or {}

    def validate(self, value: Any) -> Optional[str]:
        """Validate parameter value"""
        # Check type
        if self.type == "int" and not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return f"Parameter '{self.name}' must be an integer"

        if self.type == "float" and not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return f"Parameter '{self.name}' must be a number"

        if self.type == "bool" and not isinstance(value, bool):
            if isinstance(value, str):
                value = value.lower() in ["true", "yes", "1"]
            else:
                return f"Parameter '{self.name}' must be a boolean"

        # Check validation rules
        if "min" in self.validation and value < self.validation["min"]:
            return f"Parameter '{self.name}' must be >= {self.validation['min']}"

        if "max" in self.validation and value > self.validation["max"]:
            return f"Parameter '{self.name}' must be <= {self.validation['max']}"

        if "enum" in self.validation and value not in self.validation["enum"]:
            return f"Parameter '{self.name}' must be one of: {self.validation['enum']}"

        if "pattern" in self.validation and isinstance(value, str):
            if not re.match(self.validation["pattern"], value):
                return f"Parameter '{self.name}' does not match required pattern"

        return None


class MacroStep:
    """Represents a step in a macro"""

    def __init__(
        self,
        action: str,
        description: str = "",
        parameters: Optional[Dict] = None,
        on_error: str = "abort",
        max_retries: int = 0,
        retry_delay: int = 5,
        timeout: int = 300,
        store_result_as: Optional[str] = None,
        condition: Optional[str] = None,
        then_steps: Optional[List] = None,
        else_steps: Optional[List] = None,
        while_condition: Optional[str] = None,
        max_iterations: int = 10,
        steps: Optional[List] = None,
    ):
        self.action = action
        self.description = description
        self.parameters = parameters or {}
        self.on_error = on_error
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.store_result_as = store_result_as
        self.condition = condition
        self.then_steps = then_steps or []
        self.else_steps = else_steps or []
        self.while_condition = while_condition
        self.max_iterations = max_iterations
        self.steps = steps or []


class Macro:
    """Represents a workflow macro"""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        author: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        parameters: Optional[List[MacroParameter]] = None,
        steps: Optional[List[MacroStep]] = None,
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.tags = tags or []
        self.parameters = parameters or []
        self.steps = steps or []

    @classmethod
    def from_file(cls, file_path: Path) -> "Macro":
        """Load macro from YAML file"""
        with open(file_path) as f:
            data = yaml.safe_load(f)

        parameters = [
            MacroParameter(
                name=p["name"],
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", False),
                default=p.get("default"),
                validation=p.get("validation", {}),
            )
            for p in data.get("parameters", [])
        ]

        steps = [cls._parse_step(s) for s in data.get("steps", [])]

        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            parameters=parameters,
            steps=steps,
        )

    @classmethod
    def _parse_step(cls, step_data: Dict) -> MacroStep:
        """Parse step from dictionary"""
        return MacroStep(
            action=step_data["action"],
            description=step_data.get("description", ""),
            parameters=step_data.get("parameters", {}),
            on_error=step_data.get("on_error", "abort"),
            max_retries=step_data.get("max_retries", 0),
            retry_delay=step_data.get("retry_delay", 5),
            timeout=step_data.get("timeout", 300),
            store_result_as=step_data.get("store_as"),
            condition=step_data.get("condition"),
            then_steps=[cls._parse_step(s) for s in step_data.get("then", [])],
            else_steps=[cls._parse_step(s) for s in step_data.get("else", [])],
            while_condition=step_data.get("while"),
            max_iterations=step_data.get("max_iterations", 10),
            steps=[cls._parse_step(s) for s in step_data.get("steps", [])],
        )

    def validate_parameters(self, params: Dict) -> Optional[str]:
        """Validate macro parameters"""
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Required parameter '{param.name}' is missing"

        # Validate each provided parameter
        for param in self.parameters:
            if param.name in params:
                error = param.validate(params[param.name])
                if error:
                    return error

        return None

    def save(self, file_path: Path):
        """Save macro to YAML file"""
        data = {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "tags": self.tags,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "validation": p.validation,
                }
                for p in self.parameters
            ],
            "steps": [self._step_to_dict(s) for s in self.steps],
        }

        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _step_to_dict(self, step: MacroStep) -> Dict:
        """Convert step to dictionary"""
        result = {
            "action": step.action,
            "description": step.description,
            "parameters": step.parameters,
        }

        if step.on_error != "abort":
            result["on_error"] = step.on_error
        if step.max_retries > 0:
            result["max_retries"] = step.max_retries
        if step.store_result_as:
            result["store_as"] = step.store_result_as
        if step.condition:
            result["condition"] = step.condition
            result["then"] = [self._step_to_dict(s) for s in step.then_steps]
            result["else"] = [self._step_to_dict(s) for s in step.else_steps]
        if step.while_condition:
            result["while"] = step.while_condition
            result["max_iterations"] = step.max_iterations
            result["steps"] = [self._step_to_dict(s) for s in step.steps]

        return result


class MacroExecutionContext:
    """Context for macro execution"""

    def __init__(self, macro: Macro, parameters: Dict, voice_agent: Any):
        self.macro = macro
        self.parameters = parameters.copy()
        self.voice_agent = voice_agent
        self.variables: Dict[str, Any] = parameters.copy()
        self.step_results: List[Dict] = []
        self.current_step = 0

    def get_variable(self, name: str) -> Any:
        """Get variable value"""
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any):
        """Set variable value"""
        self.variables[name] = value

    def interpolate(self, text: str) -> str:
        """Interpolate variables in text"""
        if not isinstance(text, str):
            return text

        def replace_var(match):
            var_name = match.group(1).strip()

            # Handle expressions like {{fix_attempts + 1}}
            if any(op in var_name for op in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=', 'and', 'or']):
                try:
                    # Safely evaluate simple expressions
                    return str(self._safe_eval(var_name))
                except:
                    return match.group(0)

            value = self.get_variable(var_name)
            return str(value) if value is not None else ""

        return re.sub(r"\{\{([^}]+)\}\}", replace_var, text)

    def _safe_eval(self, expr: str) -> Any:
        """Safely evaluate simple expressions"""
        # Replace variable names with values
        for var_name, value in self.variables.items():
            expr = expr.replace(var_name, str(value))

        # Only allow safe operations
        allowed_chars = set("0123456789+-*/<>=!() andor")
        if not all(c in allowed_chars or c.isspace() for c in expr):
            raise ValueError("Unsafe expression")

        try:
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return None

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate conditional expression"""
        if not condition:
            return True

        # Interpolate variables
        condition = self.interpolate(condition)

        # Simple evaluation for common patterns
        try:
            return bool(eval(condition, {"__builtins__": {}}, {}))
        except:
            return False


class MacroEngine:
    """Executes voice command macros"""

    def __init__(self, macros_dir: str = ".claude/macros"):
        self.macros_dir = Path(macros_dir)
        self.macros: Dict[str, Macro] = {}
        self.current_execution: Optional[Dict] = None
        self._init_storage()
        self._load_macros()

    def _init_storage(self):
        """Initialize storage directory"""
        self.macros_dir.mkdir(parents=True, exist_ok=True)

    def _load_macros(self):
        """Load all macros from disk"""
        for macro_file in self.macros_dir.glob("*.yaml"):
            try:
                macro = Macro.from_file(macro_file)
                self.macros[macro.name] = macro
            except Exception as e:
                print(f"Error loading macro {macro_file}: {e}")

    def list_macros(self) -> List[Dict]:
        """List all available macros"""
        return [
            {
                "name": m.name,
                "version": m.version,
                "description": m.description,
                "tags": m.tags,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "default": p.default,
                    }
                    for p in m.parameters
                ],
            }
            for m in self.macros.values()
        ]

    def execute_macro(
        self,
        macro_name: str,
        parameters: Dict,
        voice_agent: Any,
        action_handlers: Dict[str, Callable],
    ) -> Dict:
        """Execute a macro with given parameters"""
        if macro_name not in self.macros:
            return {"error": f"Macro '{macro_name}' not found"}

        macro = self.macros[macro_name]

        # Validate parameters
        validation_error = macro.validate_parameters(parameters)
        if validation_error:
            return {"error": validation_error}

        # Fill in defaults
        for param in macro.parameters:
            if param.name not in parameters and param.default is not None:
                parameters[param.name] = param.default

        # Create execution context
        context = MacroExecutionContext(macro, parameters, voice_agent)

        # Create executor
        executor = StepExecutor(context, action_handlers)

        self.current_execution = {
            "macro_name": macro_name,
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        # Execute macro steps
        try:
            for i, step in enumerate(macro.steps):
                context.current_step = i
                result = executor.execute_step(step)

                if result.get("status") == "error" and step.on_error == "abort":
                    return {
                        "status": "error",
                        "error": result.get("error"),
                        "step": i,
                    }

            self.current_execution["status"] = "completed"
            return {
                "status": "completed",
                "results": context.step_results,
            }
        except Exception as e:
            self.current_execution["status"] = "error"
            return {
                "status": "error",
                "error": str(e),
                "step": context.current_step,
            }
        finally:
            self.current_execution = None

    def create_macro(self, definition: Dict) -> Dict:
        """Create new macro from definition"""
        try:
            macro = Macro(
                name=definition["name"],
                version=definition.get("version", "1.0.0"),
                author=definition.get("author", ""),
                description=definition.get("description", ""),
                tags=definition.get("tags", []),
            )

            # Save to disk
            macro_file = self.macros_dir / f"{macro.name}.yaml"
            macro.save(macro_file)

            # Add to loaded macros
            self.macros[macro.name] = macro

            return {"status": "created", "name": macro.name}
        except Exception as e:
            return {"error": str(e)}

    def delete_macro(self, macro_name: str) -> Dict:
        """Delete a macro"""
        if macro_name not in self.macros:
            return {"error": f"Macro '{macro_name}' not found"}

        # Remove from disk
        macro_file = self.macros_dir / f"{macro_name}.yaml"
        if macro_file.exists():
            macro_file.unlink()

        # Remove from loaded macros
        del self.macros[macro_name]

        return {"status": "deleted"}


class StepExecutor:
    """Executes individual macro steps"""

    def __init__(self, context: MacroExecutionContext, action_handlers: Dict[str, Callable]):
        self.context = context
        self.action_handlers = action_handlers

    def execute_step(self, step: MacroStep) -> Dict:
        """Execute a single step"""
        # Interpolate parameters
        params = {}
        for key, value in step.parameters.items():
            if isinstance(value, str):
                params[key] = self.context.interpolate(value)
            else:
                params[key] = value

        # Execute based on action type
        if step.action == "conditional":
            return self._execute_conditional(step)
        elif step.action == "loop":
            return self._execute_loop(step)
        elif step.action == "wait":
            return self._execute_wait(params)
        elif step.action == "set_variable":
            return self._execute_set_variable(params)
        elif step.action == "log":
            return self._execute_log(params)
        else:
            # Use provided action handler
            if step.action in self.action_handlers:
                result = self._execute_with_retry(step, params)

                # Store result if requested
                if step.store_result_as and result.get("status") != "error":
                    self.context.set_variable(step.store_result_as, result)

                return result
            else:
                return {"status": "error", "error": f"Unknown action: {step.action}"}

    def _execute_with_retry(self, step: MacroStep, params: Dict) -> Dict:
        """Execute action with retry logic"""
        handler = self.action_handlers[step.action]
        attempts = 0
        max_attempts = step.max_retries + 1

        while attempts < max_attempts:
            try:
                result = handler(**params)
                if result.get("status") != "error":
                    return result

                if attempts < max_attempts - 1:
                    time.sleep(step.retry_delay)
                    attempts += 1
                else:
                    return result
            except Exception as e:
                if attempts < max_attempts - 1:
                    time.sleep(step.retry_delay)
                    attempts += 1
                else:
                    return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "Max retries exceeded"}

    def _execute_conditional(self, step: MacroStep) -> Dict:
        """Execute conditional step"""
        condition_met = self.context.evaluate_condition(step.condition)

        steps_to_execute = step.then_steps if condition_met else step.else_steps

        for sub_step in steps_to_execute:
            result = self.execute_step(sub_step)
            if result.get("status") == "error":
                return result

        return {"status": "success"}

    def _execute_loop(self, step: MacroStep) -> Dict:
        """Execute loop step"""
        iterations = 0

        while iterations < step.max_iterations:
            if step.while_condition:
                if not self.context.evaluate_condition(step.while_condition):
                    break

            for sub_step in step.steps:
                result = self.execute_step(sub_step)
                if result.get("status") == "error":
                    return result

            iterations += 1

        return {"status": "success", "iterations": iterations}

    def _execute_wait(self, params: Dict) -> Dict:
        """Wait for specified duration"""
        seconds = params.get("seconds", 1)
        time.sleep(seconds)
        return {"status": "success"}

    def _execute_set_variable(self, params: Dict) -> Dict:
        """Set variable value"""
        name = params.get("name")
        value = params.get("value")

        if name:
            self.context.set_variable(name, value)
            return {"status": "success"}

        return {"status": "error", "error": "Missing variable name"}

    def _execute_log(self, params: Dict) -> Dict:
        """Log message"""
        message = params.get("message", "")
        print(f"[MACRO LOG] {message}")
        return {"status": "success"}
