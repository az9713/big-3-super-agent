# Feature: Voice Command Macros & Workflow Templates

## Executive Summary

**Voice Command Macros** enable users to define and execute complex multi-step workflows with a single voice command. Instead of issuing 10+ sequential commands, users can create reusable macros that automate entire workflows, complete with conditional logic, error handling, and retry mechanisms.

**Target Users**: Developers who frequently repeat similar command sequences

**Expected Benefits**:
- **10x faster workflows**: One command instead of 10+
- **Zero mistakes**: Consistent execution every time
- **Knowledge sharing**: Teams can share proven workflows
- **Reduced cognitive load**: No need to remember command sequences

---

## Problem Statement

### Current Pain Points

Users frequently repeat the same command sequences:

**Example 1: Video Generation Pipeline**
```
1. "Create agent video-creator"
2. "Command video-creator to create a sora-2 video with prompt: mountains"
3. "Check video-creator result"
4. [Wait 30 seconds]
5. "Check video-creator result"
6. [Wait 30 seconds]
7. "Check video-creator result"
8. "Open the generated video"
9. "Delete video-creator agent"
```

**Example 2: Test-Fix-Commit Cycle**
```
1. "Create agent tester"
2. "Command tester to run all tests"
3. "Check tester result"
4. [If tests fail]
5. "Command tester to fix the failures"
6. "Check tester result"
7. "Command tester to run tests again"
8. "Check tester result"
9. [Repeat until passing]
10. "Command tester to commit changes"
11. "Delete tester agent"
```

**Example 3: PR Review Process**
```
1. "Create agent reviewer"
2. "Command reviewer to review PR #123"
3. "Check reviewer result"
4. "Create agent tester"
5. "Command tester to run all tests"
6. "Check tester result"
7. "Command reviewer to approve PR"
8. "Delete reviewer and tester agents"
```

### Impact

- **Cognitive load**: Users must remember exact command sequences
- **Time waste**: 5-10 minutes per repetitive workflow
- **Errors**: Forgetting steps or using wrong parameters
- **No reusability**: Can't save or share workflows
- **Inconsistency**: Different approaches each time

---

## Solution Overview

### Core Concept

A **Voice Macro** is a YAML-defined workflow that:
- Accepts parameters (e.g., video prompt, PR number)
- Executes a sequence of commands
- Supports conditionals and loops
- Handles errors with retry logic
- Provides progress updates

### Key Capabilities

1. **Macro Definition**
   - YAML-based configuration
   - Support for variables and parameters
   - Conditional branching (if/else)
   - Loops (retry, for-each)
   - Error handling strategies

2. **Template Library**
   - Pre-built macros for common workflows
   - Community marketplace for sharing
   - Import/export functionality
   - Version control integration

3. **Interactive Execution**
   - Pause for user input at specific steps
   - Progress reporting
   - Real-time updates
   - Rollback on failure

4. **Macro Management**
   - List, create, edit, delete macros
   - Macro validation
   - Usage analytics
   - Macro recommendations

---

## Macro Definition Format

### Basic Structure

```yaml
# Macro metadata
name: macro-name
version: 1.0.0
author: user@example.com
description: What this macro does
tags: [video, automation, testing]

# Input parameters
parameters:
  - name: param_name
    type: string  # string, int, float, bool, list
    description: Parameter description
    required: true
    default: optional_default_value
    validation:
      pattern: "regex-pattern"  # For strings
      min: 0  # For numbers
      max: 100
      enum: [option1, option2]  # Allowed values

# Workflow steps
steps:
  - action: action_name
    description: What this step does
    parameters:
      param1: value
      param2: "{{variable}}"  # Variable interpolation
    on_error: continue  # continue, retry, abort, skip
    max_retries: 3
    retry_delay: 5  # seconds
    timeout: 300  # seconds
    store_result_as: variable_name  # Store result for later use

  # Conditional execution
  - action: conditional
    condition: "{{variable}} == 'value'"
    then:
      - action: ...
    else:
      - action: ...

  # Loop execution
  - action: loop
    while: "{{condition}}"
    max_iterations: 10
    steps:
      - action: ...

  # User interaction
  - action: prompt_user
    message: "Please confirm: {{summary}}"
    store_as: user_response
```

### Built-in Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `create_agent` | Create new agent | `agent_name`, `tool`, `type`, `working_directory` |
| `command_agent` | Send command to agent | `agent_name`, `prompt` |
| `check_agent_result` | Get agent results | `agent_name`, `store_as` |
| `delete_agent` | Remove agent | `agent_name` |
| `browser_use` | Browser automation | `task`, `store_as` |
| `read_file` | Read file contents | `file_path`, `store_as` |
| `wait` | Sleep for duration | `seconds` |
| `conditional` | If/else branching | `condition`, `then`, `else` |
| `loop` | Repeat steps | `while`, `max_iterations`, `steps` |
| `prompt_user` | Ask user for input | `message`, `store_as` |
| `set_variable` | Set variable value | `name`, `value` |
| `log` | Print message | `message` |
| `goto_step` | Jump to step | `step_index` |
| `exit` | End macro execution | `message` |

---

## Example Macros

### Example 1: Video Generation Pipeline

```yaml
name: generate-and-review-video
version: 1.0.0
description: Create Sora video, wait for completion, open for review
tags: [video, sora, automation]

parameters:
  - name: prompt
    type: string
    description: Video prompt
    required: true

  - name: model
    type: string
    description: Sora model to use
    default: sora-2
    validation:
      enum: [sora-2, sora-2-pro]

  - name: duration
    type: int
    description: Video duration in seconds
    default: 4
    validation:
      enum: [4, 8, 12]

  - name: resolution
    type: string
    description: Video resolution
    default: "1280x720"
    validation:
      enum: ["1280x720", "720x1280", "1024x1024", "1920x1080"]

steps:
  # Create agent
  - action: create_agent
    description: Create video generation agent
    parameters:
      agent_name: video_creator
      tool: claude_code
      type: agentic_coding
    on_error: abort

  # Command agent to create video
  - action: command_agent
    description: Start video generation
    parameters:
      agent_name: video_creator
      prompt: |
        Create a {{model}} video with the following parameters:
        - Prompt: {{prompt}}
        - Duration: {{duration}} seconds
        - Resolution: {{resolution}}

        Use the Content-Gen backend API at http://localhost:4444/api/v1/videos
        Return the video ID when generation starts.
    store_result_as: command_result

  # Wait for agent to start generation
  - action: wait
    parameters:
      seconds: 5

  # Poll for completion
  - action: loop
    description: Wait for video completion
    while: "{{video_status}} != 'completed'"
    max_iterations: 60
    steps:
      - action: check_agent_result
        parameters:
          agent_name: video_creator
          store_as: agent_result

      - action: set_variable
        parameters:
          name: video_status
          value: "{{agent_result.video_status}}"

      - action: log
        parameters:
          message: "Video status: {{video_status}}, progress: {{agent_result.progress}}%"

      - action: conditional
        condition: "{{video_status}} == 'failed'"
        then:
          - action: exit
            parameters:
              message: "Video generation failed: {{agent_result.error}}"

      - action: conditional
        condition: "{{video_status}} != 'completed'"
        then:
          - action: wait
            parameters:
              seconds: 10

  # Open video in browser
  - action: browser_use
    description: Open generated video
    parameters:
      task: "Navigate to http://localhost:3333 and play the most recent video"

  # Cleanup
  - action: delete_agent
    parameters:
      agent_name: video_creator
```

**Usage**:
```
User: "Run macro generate-and-review-video with prompt 'sunset over mountains',
       model sora-2-pro, duration 8"
```

### Example 2: Test-Fix-Commit Cycle

```yaml
name: test-fix-commit
version: 1.0.0
description: Run tests, fix failures, commit when passing
tags: [testing, ci, automation]

parameters:
  - name: test_command
    type: string
    description: Command to run tests
    default: "pytest"

  - name: max_fix_attempts
    type: int
    description: Maximum fix attempts
    default: 3

  - name: commit_message
    type: string
    description: Commit message (optional, will auto-generate if not provided)
    required: false

steps:
  # Create tester agent
  - action: create_agent
    parameters:
      agent_name: tester
      tool: claude_code
      type: agentic_coding

  # Run tests (first attempt)
  - action: command_agent
    parameters:
      agent_name: tester
      prompt: "Run tests using: {{test_command}}"

  - action: wait
    parameters:
      seconds: 5

  - action: check_agent_result
    parameters:
      agent_name: tester
      store_as: test_result

  # Fix loop
  - action: set_variable
    parameters:
      name: fix_attempts
      value: 0

  - action: loop
    while: "{{test_result.status}} == 'failed' and {{fix_attempts}} < {{max_fix_attempts}}"
    max_iterations: "{{max_fix_attempts}}"
    steps:
      - action: set_variable
        parameters:
          name: fix_attempts
          value: "{{fix_attempts + 1}}"

      - action: log
        parameters:
          message: "Tests failed. Fix attempt {{fix_attempts}}/{{max_fix_attempts}}"

      - action: command_agent
        parameters:
          agent_name: tester
          prompt: |
            The tests failed with the following errors:
            {{test_result.errors}}

            Please fix all test failures.

      - action: wait
        parameters:
          seconds: 10

      - action: check_agent_result
        parameters:
          agent_name: tester
          store_as: fix_result

      # Run tests again
      - action: command_agent
        parameters:
          agent_name: tester
          prompt: "Run tests again using: {{test_command}}"

      - action: wait
        parameters:
          seconds: 5

      - action: check_agent_result
        parameters:
          agent_name: tester
          store_as: test_result

  # Check final test status
  - action: conditional
    condition: "{{test_result.status}} == 'failed'"
    then:
      - action: log
        parameters:
          message: "⚠️  Could not fix all test failures after {{max_fix_attempts}} attempts"
      - action: exit
        parameters:
          message: "Tests still failing. Manual intervention required."

  # Tests passed - commit changes
  - action: log
    parameters:
      message: "✓ All tests passing! Committing changes..."

  - action: conditional
    condition: "{{commit_message}} == ''"
    then:
      # Auto-generate commit message
      - action: command_agent
        parameters:
          agent_name: tester
          prompt: |
            Generate a semantic commit message for the changes that fixed the tests.
            Follow conventional commits format.
      - action: check_agent_result
        parameters:
          agent_name: tester
          store_as: commit_result
      - action: set_variable
        parameters:
          name: final_commit_message
          value: "{{commit_result.commit_message}}"
    else:
      - action: set_variable
        parameters:
          name: final_commit_message
          value: "{{commit_message}}"

  # Commit with final message
  - action: command_agent
    parameters:
      agent_name: tester
      prompt: |
        Commit all changes with this message:
        {{final_commit_message}}

  # Cleanup
  - action: delete_agent
    parameters:
      agent_name: tester

  - action: log
    parameters:
      message: "✓ All done! Tests passing and changes committed."
```

**Usage**:
```
User: "Run macro test-fix-commit with test_command 'npm test'"
```

### Example 3: PR Review and Merge

```yaml
name: review-and-merge-pr
version: 1.0.0
description: Review PR, run tests, merge if approved
tags: [pr, review, git]

parameters:
  - name: pr_number
    type: int
    description: Pull request number
    required: true

  - name: run_tests
    type: bool
    description: Run tests before merging
    default: true

  - name: require_approval
    type: bool
    description: Require user approval before merging
    default: true

steps:
  # Create reviewer agent
  - action: create_agent
    parameters:
      agent_name: reviewer
      tool: claude_code
      type: agentic_coding

  # Review PR
  - action: command_agent
    parameters:
      agent_name: reviewer
      prompt: |
        Review pull request #{{pr_number}}:
        1. Check code quality
        2. Look for security issues
        3. Verify tests are included
        4. Check documentation

        Provide a detailed review with:
        - Summary of changes
        - Issues found (if any)
        - Recommendation (approve, request changes, or reject)

  - action: wait
    parameters:
      seconds: 10

  - action: check_agent_result
    parameters:
      agent_name: reviewer
      store_as: review_result

  # Log review summary
  - action: log
    parameters:
      message: |
        Review complete:
        {{review_result.summary}}

        Recommendation: {{review_result.recommendation}}

  # Check if changes requested
  - action: conditional
    condition: "{{review_result.recommendation}} == 'reject'"
    then:
      - action: log
        parameters:
          message: "❌ PR rejected. Issues found:\n{{review_result.issues}}"
      - action: delete_agent
        parameters:
          agent_name: reviewer
      - action: exit
        parameters:
          message: "PR review failed. Please address issues."

  # Run tests if requested
  - action: conditional
    condition: "{{run_tests}} == true"
    then:
      - action: create_agent
        parameters:
          agent_name: tester
          tool: claude_code
          type: agentic_coding

      - action: command_agent
        parameters:
          agent_name: tester
          prompt: "Checkout PR #{{pr_number}} and run all tests"

      - action: wait
        parameters:
          seconds: 15

      - action: check_agent_result
        parameters:
          agent_name: tester
          store_as: test_result

      - action: conditional
        condition: "{{test_result.status}} == 'failed'"
        then:
          - action: log
            parameters:
              message: "❌ Tests failed:\n{{test_result.errors}}"
          - action: delete_agent
            parameters:
              agent_name: reviewer
          - action: delete_agent
            parameters:
              agent_name: tester
          - action: exit
            parameters:
              message: "Tests failing. Cannot merge."

      - action: log
        parameters:
          message: "✓ All tests passed"

      - action: delete_agent
        parameters:
          agent_name: tester

  # Get user approval if required
  - action: conditional
    condition: "{{require_approval}} == true"
    then:
      - action: prompt_user
        parameters:
          message: |
            PR #{{pr_number}} review complete:
            - Code quality: {{review_result.code_quality}}
            - Tests: {{test_result.status or 'skipped'}}
            - Recommendation: {{review_result.recommendation}}

            Approve and merge? (yes/no)
          store_as: user_approval

      - action: conditional
        condition: "{{user_approval}} != 'yes'"
        then:
          - action: delete_agent
            parameters:
              agent_name: reviewer
          - action: exit
            parameters:
              message: "Merge cancelled by user"

  # Merge PR
  - action: command_agent
    parameters:
      agent_name: reviewer
      prompt: "Merge PR #{{pr_number}} with squash commit"

  - action: wait
    parameters:
      seconds: 5

  - action: check_agent_result
    parameters:
      agent_name: reviewer
      store_as: merge_result

  # Cleanup
  - action: delete_agent
    parameters:
      agent_name: reviewer

  - action: log
    parameters:
      message: "✓ PR #{{pr_number}} merged successfully!"
```

**Usage**:
```
User: "Run macro review-and-merge-pr with pr_number 123"
```

---

## Implementation Details

### Macro Engine

```python
class MacroEngine:
    """Executes voice command macros"""

    def __init__(self, voice_agent: OpenAIRealtimeVoiceAgent):
        self.voice_agent = voice_agent
        self.macros_dir = Path(".claude/macros")
        self.macros: dict[str, Macro] = {}
        self.current_execution: MacroExecution | None = None
        self._load_macros()

    def _load_macros(self):
        """Load all macros from disk"""
        if not self.macros_dir.exists():
            self.macros_dir.mkdir(parents=True)

        for macro_file in self.macros_dir.glob("*.yaml"):
            try:
                macro = Macro.from_file(macro_file)
                self.macros[macro.name] = macro
            except Exception as e:
                print(f"Error loading macro {macro_file}: {e}")

    def list_macros(self) -> list[dict]:
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
        parameters: dict,
    ) -> dict:
        """Execute a macro with given parameters"""
        if macro_name not in self.macros:
            return {"error": f"Macro '{macro_name}' not found"}

        macro = self.macros[macro_name]

        # Validate parameters
        validation_error = macro.validate_parameters(parameters)
        if validation_error:
            return {"error": validation_error}

        # Create execution context
        context = MacroExecutionContext(
            macro=macro,
            parameters=parameters,
            voice_agent=self.voice_agent,
        )

        self.current_execution = MacroExecution(context)

        # Execute macro
        try:
            result = self.current_execution.run()
            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "step": self.current_execution.current_step,
            }
        finally:
            self.current_execution = None

    def create_macro(self, definition: dict) -> dict:
        """Create new macro from definition"""
        try:
            macro = Macro.from_dict(definition)

            # Validate macro
            validation_error = macro.validate()
            if validation_error:
                return {"error": validation_error}

            # Save to disk
            macro_file = self.macros_dir / f"{macro.name}.yaml"
            macro.save(macro_file)

            # Add to loaded macros
            self.macros[macro.name] = macro

            return {"status": "created", "name": macro.name}
        except Exception as e:
            return {"error": str(e)}

    def delete_macro(self, macro_name: str) -> dict:
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
```

### Macro Execution Context

```python
class MacroExecutionContext:
    """Context for macro execution"""

    def __init__(
        self,
        macro: Macro,
        parameters: dict,
        voice_agent: OpenAIRealtimeVoiceAgent,
    ):
        self.macro = macro
        self.parameters = parameters
        self.voice_agent = voice_agent
        self.variables: dict[str, any] = parameters.copy()
        self.step_results: list[dict] = []

    def get_variable(self, name: str) -> any:
        """Get variable value"""
        return self.variables.get(name)

    def set_variable(self, name: str, value: any):
        """Set variable value"""
        self.variables[name] = value

    def interpolate(self, text: str) -> str:
        """Interpolate variables in text"""
        # Replace {{variable_name}} with actual values
        import re

        def replace_var(match):
            var_name = match.group(1)
            return str(self.get_variable(var_name) or "")

        return re.sub(r"{{([^}]+)}}", replace_var, text)

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate conditional expression"""
        # Interpolate variables
        condition = self.interpolate(condition)

        # Safe evaluation (restricted to comparisons and logic)
        try:
            # This is simplified - production would use safer eval
            return eval(condition, {"__builtins__": {}}, {})
        except:
            return False
```

### Step Executor

```python
class StepExecutor:
    """Executes individual macro steps"""

    def __init__(self, context: MacroExecutionContext):
        self.context = context

    def execute_step(self, step: Step) -> dict:
        """Execute a single step"""
        action = step.action

        # Interpolate all parameters
        params = {}
        for key, value in step.parameters.items():
            if isinstance(value, str):
                params[key] = self.context.interpolate(value)
            else:
                params[key] = value

        # Execute action
        if action == "create_agent":
            return self._create_agent(params)
        elif action == "command_agent":
            return self._command_agent(params)
        elif action == "check_agent_result":
            return self._check_agent_result(params)
        elif action == "delete_agent":
            return self._delete_agent(params)
        elif action == "browser_use":
            return self._browser_use(params)
        elif action == "wait":
            return self._wait(params)
        elif action == "conditional":
            return self._conditional(step, params)
        elif action == "loop":
            return self._loop(step, params)
        elif action == "set_variable":
            return self._set_variable(params)
        elif action == "log":
            return self._log(params)
        elif action == "prompt_user":
            return self._prompt_user(params)
        else:
            return {"error": f"Unknown action: {action}"}

    def _create_agent(self, params: dict) -> dict:
        """Create agent"""
        result = self.context.voice_agent.create_agent(
            tool=params["tool"],
            type=params["type"],
            agent_name=params["agent_name"],
            working_directory=params.get("working_directory"),
        )
        return {"status": "success", "result": result}

    def _command_agent(self, params: dict) -> dict:
        """Command agent"""
        result = self.context.voice_agent.command_agent(
            agent_name=params["agent_name"],
            prompt=params["prompt"],
        )
        return {"status": "success", "result": result}

    # ... other action implementations
```

---

## Voice Agent Integration

### New Tools

```python
{
    "type": "function",
    "name": "run_macro",
    "description": "Execute a saved workflow macro",
    "parameters": {
        "type": "object",
        "properties": {
            "macro_name": {"type": "string"},
            "parameters": {
                "type": "object",
                "description": "Macro parameters as key-value pairs",
            },
        },
        "required": ["macro_name"],
    },
},
{
    "type": "function",
    "name": "list_macros",
    "description": "List all available macros",
    "parameters": {"type": "object", "properties": {}},
},
{
    "type": "function",
    "name": "create_macro",
    "description": "Create new macro from definition",
    "parameters": {
        "type": "object",
        "properties": {
            "definition": {
                "type": "object",
                "description": "Macro definition in JSON format",
            },
        },
        "required": ["definition"],
    },
},
{
    "type": "function",
    "name": "delete_macro",
    "description": "Delete a macro",
    "parameters": {
        "type": "object",
        "properties": {
            "macro_name": {"type": "string"},
        },
        "required": ["macro_name"],
    },
},
```

---

## Benefits

### Time Savings

| Workflow | Manual Commands | With Macro | Time Saved |
|----------|----------------|------------|------------|
| Video generation pipeline | 9 commands, 5 min | 1 command, 30 sec | 90% |
| Test-fix-commit cycle | 10+ commands, 15 min | 1 command, 2 min | 87% |
| PR review process | 8 commands, 10 min | 1 command, 1 min | 90% |

### Error Reduction

- **100% consistency**: Same steps every time
- **Built-in validation**: Parameter validation prevents errors
- **Error handling**: Automatic retry and recovery
- **No missed steps**: Complete workflows guaranteed

### Knowledge Sharing

- **Team library**: Share proven workflows
- **Onboarding**: New developers learn best practices
- **Documentation**: Macros serve as executable documentation
- **Continuous improvement**: Iterate on shared macros

---

## Success Metrics

- Number of macros created per user
- % of commands that are macro invocations
- Average time saved per macro execution
- Macro reuse rate (same macro used multiple times)
- User satisfaction (1-5 rating)

---

## Conclusion

Voice Command Macros transform repetitive multi-step workflows into single-command operations, delivering **10x productivity gains** through automation, consistency, and reusability.
