# Quick Start Guide - New Features (v2.0 + v2.1 + v2.2 + v2.3)

This guide helps you quickly get started with all eleven features (v2.0: 5 features, v2.1: 2 features, v2.2: 2 features, v2.3: 2 features).

## Prerequisites

All features are implemented as Python modules in `apps/realtime-poc/features/`. They work independently and can be used directly without voice integration.

## Feature 1: Multi-Agent Collaboration Rooms

### Quick Test

```python
# Run from project root
cd /home/user/big-3-super-agent
python3

>>> from apps.realtime_poc.features.collaboration_rooms import CollaborationRoomManager
>>>
>>> # Create manager
>>> mgr = CollaborationRoomManager()
>>>
>>> # Create a room
>>> result = mgr.create_room("test-room", "Testing collaboration rooms")
>>> print(f"Created room: {result}")
>>>
>>> # Add agents
>>> mgr.add_agent_to_room("test-room", "agent1", "developer", "claude_code")
>>> mgr.add_agent_to_room("test-room", "agent2", "tester", "gemini")
>>>
>>> # Add a task
>>> task = mgr.room_command("test-room", "Build a feature", assign_to="agent1")
>>> print(f"Task created: {task}")
>>>
>>> # Check status
>>> status = mgr.get_room_status("test-room")
>>> print(f"Room has {len(status['agents'])} agents")
>>> print(f"Tasks: {status['tasks']}")
>>>
>>> # List all rooms
>>> rooms = mgr.list_rooms()
>>> for room in rooms:
...     print(f"- {room['name']}: {room['agents']} agents, {room['tasks']} tasks")
```

### Key Files Created

- Registry: `apps/content-gen/agents/collaboration_rooms/registry.json`
- Operator Log: `apps/content-gen/agents/collaboration_rooms/test-room/operator_log.md`
- Screenshots: `apps/content-gen/agents/collaboration_rooms/test-room/screenshots/`

---

## Feature 2: Voice Command Macros

### Quick Test

First, create a simple macro:

```bash
mkdir -p .claude/macros
cat > .claude/macros/hello-world.yaml <<'EOF'
name: hello-world
version: 1.0.0
description: Simple test macro
tags: [test]

parameters:
  - name: name
    type: string
    default: "World"

steps:
  - action: log
    parameters:
      message: "Hello, {{name}}!"

  - action: set_variable
    parameters:
      name: greeting
      value: "Hi there!"

  - action: log
    parameters:
      message: "{{greeting}}"
EOF
```

Now test it:

```python
>>> from apps.realtime_poc.features.macros import MacroEngine
>>>
>>> # Initialize engine
>>> engine = MacroEngine(macros_dir=".claude/macros")
>>>
>>> # List macros
>>> macros = engine.list_macros()
>>> for macro in macros:
...     print(f"- {macro['name']}: {macro['description']}")
>>>
>>> # Execute macro
>>> result = engine.execute_macro(
...     macro_name="hello-world",
...     parameters={"name": "Developer"},
...     voice_agent=None,  # Not needed for this simple macro
...     action_handlers={},  # No external actions
... )
>>> print(f"Result: {result}")
```

### Example Macros Provided

Check `docs/features/02-voice-command-macros.md` for complete macro examples including:
- Video generation pipeline
- Test-fix-commit cycle
- PR review process

---

## Feature 3: Performance Analytics

### Quick Test

```python
>>> from apps.realtime_poc.features.analytics import MetricsCollector, AnalyticsDashboard
>>>
>>> # Initialize collector
>>> metrics = MetricsCollector(db_path="analytics/metrics.db")
>>>
>>> # Track a task
>>> metrics.track_task_start(
...     task_id="task-001",
...     agent_name="test-agent",
...     agent_tool="claude_code",
...     task_type="code_editing",
...     task_description="Test task",
...     project="test-project",
... )
>>>
>>> # Simulate task completion
>>> import time
>>> time.sleep(2)
>>>
>>> metrics.track_task_end(
...     task_id="task-001",
...     status="completed",
...     prompt_tokens=1000,
...     completion_tokens=500,
...     cost_usd=0.015,
... )
>>>
>>> # Get metrics
>>> today_metrics = metrics.get_metrics("today", "all")
>>> print(f"Tasks today: {today_metrics['tasks']['total_tasks']}")
>>> print(f"Total cost: ${today_metrics['cost']['total_cost']}")
>>>
>>> # Get dashboard summary
>>> dashboard = AnalyticsDashboard(metrics)
>>> summary = dashboard.get_summary("today")
>>> print(summary)
>>>
>>> # Get recommendations
>>> recommendations = dashboard.get_recommendations()
>>> print(recommendations)
```

### Key Files Created

- Database: `analytics/metrics.db` (SQLite)
- Tables: `task_executions`, `agents`, `daily_summaries`, `recommendations`

---

## Feature 4: Interactive Voice Code Review

### Quick Test

```python
>>> from apps.realtime_poc.features.code_review import VoiceCodeReviewSession, CodeAnalyzer
>>>
>>> # Analyze a single file
>>> analyzer = CodeAnalyzer()
>>> findings = analyzer.analyze_file("apps/realtime-poc/features/code_review.py")
>>> print(f"Found {len(findings)} issues")
>>>
>>> # Show findings by severity
>>> for severity in ["critical", "high", "medium", "low"]:
...     issues = [f for f in findings if f.severity == severity]
...     if issues:
...         print(f"\n{severity.upper()} ({len(issues)}):")
...         for f in issues[:3]:
...             print(f"  - Line {f.line}: {f.title}")
>>>
>>> # Start a review session
>>> session = VoiceCodeReviewSession("apps/realtime-poc/features")
>>> result = session.start_review()
>>> print(f"Review started: {result}")
>>>
>>> # Get current finding
>>> finding = session.get_current_finding()
>>> if finding:
...     f = finding['finding']
...     print(f"\nIssue {finding['index']}/{finding['total']}:")
...     print(f"  File: {f['file']}")
...     print(f"  Line: {f['line']}")
...     print(f"  {f['severity'].upper()}: {f['title']}")
...     print(f"  {f['description']}")
...     print(f"  Recommendation: {f['recommendation']}")
>>>
>>> # Get summary
>>> summary = session.get_summary()
>>> print(f"\nSummary:")
>>> print(f"  Total findings: {summary['total_findings']}")
>>> print(f"  By severity: {summary['by_severity']}")
```

### What It Detects

- **Security**: SQL injection, hardcoded secrets, eval usage, shell injection
- **Performance**: Nested loops, repeated function calls
- **Style**: Line length, missing docstrings
- **More analyzers can be easily added**

---

## Feature 5: Intelligent Git Assistant

### Quick Test

```python
>>> from apps.realtime_poc.features.git_assistant import GitAssistant
>>>
>>> # Initialize assistant
>>> git = GitAssistant(repo_path=".")
>>>
>>> # Get git status
>>> status = git.get_status()
>>> print(f"Staged: {len(status['staged'])} files")
>>> print(f"Unstaged: {len(status['unstaged'])} files")
>>> print(f"Untracked: {len(status['untracked'])} files")
>>>
>>> # Get diff (if you have staged changes)
>>> if status['staged']:
...     diff = git.get_staged_diff()
...     print(f"Diff: {len(diff)} characters")
...
...     # Generate commit message
...     message = git.generate_commit_message(diff)
...     print(f"\nSuggested commit message:\n{message}")
>>>
>>> # Generate PR description (if on feature branch)
>>> pr_data = git.generate_pr_description(base_branch="main")
>>> print(f"\nPR Title: {pr_data['title']}")
>>> print(f"Description:\n{pr_data['description'][:200]}...")
>>>
>>> # Check for conflicts
>>> conflicts = git.detect_conflicts()
>>> if conflicts['has_conflicts']:
...     print(f"⚠ Conflicts in: {conflicts['files']}")
... else:
...     print("✓ No conflicts")
```

### Example Operations

```python
# Create a feature branch
>>> result = git.create_branch("add-feature-x", "feature")
>>> print(result)

# Commit with auto-generated message (requires staged changes)
>>> result = git.smart_commit(auto_message=True)
>>> if result.get("status") == "committed":
...     print(f"✓ Committed: {result['hash']}")

# Push changes
>>> result = git.push_changes(remote="origin")
>>> print(result)
```

---

## Feature 6: Voice-Activated Debugging Assistant (v2.1)

### Quick Test

```python
>>> from apps.realtime_poc.features.debugging import DebuggingSession
>>>
>>> # Initialize session
>>> session = DebuggingSession()
>>>
>>> # Analyze an error
>>> error_text = """
... Traceback (most recent call last):
...   File "app.py", line 42, in process_data
...     result = data['key']
... KeyError: 'key'
... """
>>>
>>> analysis = session.analyze_error(error_text)
>>> print(f"Error: {analysis['error_type']}")
>>> print(f"Severity: {analysis['severity']}")
>>>
>>> # Get likely causes
>>> print("\nLikely Causes:")
>>> for cause in analysis['likely_causes']:
...     print(f"  - {cause}")
>>>
>>> # Get fix suggestions
>>> print("\nSuggested Fixes:")
>>> for fix in analysis['suggested_fixes']:
...     print(f"  - {fix}")
>>>
>>> # Generate fix code
>>> fix_code = session.generate_fix_code()
>>> print(f"\nGenerated Fix:\n{fix_code[:200]}...")
>>>
>>> # Suggest breakpoints
>>> breakpoints = session.suggest_breakpoints()
>>> print("\nBreakpoint Suggestions:")
>>> for bp in breakpoints[:3]:
...     print(f"  {bp['file']}:{bp['line']} - {bp['reason']}")
```

### Log Analysis Example

```python
>>> from apps.realtime_poc.features.debugging import LogAnalyzer
>>>
>>> analyzer = LogAnalyzer()
>>>
>>> # Analyze logs for errors
>>> result = analyzer.analyze_logs("/var/log/app.log", recent_lines=100)
>>> print(f"Total Errors: {result['total_errors']}")
>>> print(f"Total Warnings: {result['total_warnings']}")
>>>
>>> # Show error groups
>>> print("\nError Groups:")
>>> for error_type, count in result['error_groups'].items():
...     print(f"  {error_type}: {count}")
>>>
>>> # Search logs for specific term
>>> matches = analyzer.search_logs("/var/log/app.log", "database", context_lines=2)
>>> print(f"\nFound {len(matches)} matches")
>>> if matches:
...     print(f"First match: {matches[0]['match']}")
```

### What It Does

- **Stack Trace Parsing**: Extracts error type, message, and stack frames from Python tracebacks
- **Root Cause Analysis**: Matches error patterns to known issues and suggests likely causes
- **Fix Generation**: Creates code snippets to fix common errors (AttributeError, KeyError, etc.)
- **Log Analysis**: Finds errors in log files, groups by type, extracts timestamps
- **Breakpoint Suggestions**: Recommends optimal debugging locations based on stack analysis
- **Interactive Sessions**: Manages complete debugging workflows

---

## Feature 7: Natural Language Testing Framework (v2.1)

### Quick Test

```python
>>> from apps.realtime_poc.features.testing import TestingSession
>>>
>>> # Initialize session
>>> session = TestingSession(project_root=".")
>>>
>>> # Generate a test from natural language
>>> result = session.create_and_run_test(
...     test_description="Test that user login validates email format",
...     target_file="backend/auth.py",
...     language="python",
...     auto_run=False  # Don't run automatically for this demo
... )
>>>
>>> print(f"Test File: {result['test_file_written']}")
>>> print(f"\nGenerated Test Code:")
>>> print(result['test_code'][:300])
>>>
>>> # Run all tests with coverage
>>> all_results = session.run_all_tests(language="python", coverage=True)
>>> print(f"\nAll Tests:")
>>> print(f"  Total: {all_results['total']}")
>>> print(f"  Passed: {all_results['passed']}")
>>> print(f"  Failed: {all_results['failed']}")
>>>
>>> # Get coverage report
>>> if 'coverage_analysis' in all_results:
...     coverage_pct = all_results['coverage_analysis']['overall_coverage']
...     print(f"  Coverage: {coverage_pct}%")
```

### Coverage Analysis Example

```python
>>> from apps.realtime_poc.features.testing import CoverageAnalyzer
>>>
>>> analyzer = CoverageAnalyzer(project_root=".")
>>>
>>> # Analyze Python coverage
>>> coverage = analyzer.analyze_python_coverage("coverage.json")
>>> print(f"Overall Coverage: {coverage['overall_coverage']}%")
>>>
>>> # Get files with low coverage
>>> print("\nFiles with Low Coverage:")
>>> for file_data in coverage['coverage_gaps'][:5]:
...     print(f"  {file_data['file']}: {file_data['coverage']}%")
...     print(f"    Missing {file_data['missing']} lines")
>>>
>>> # Get test suggestions
>>> suggestions = analyzer.suggest_missing_tests(coverage)
>>> print("\nTest Suggestions:")
>>> for suggestion in suggestions[:3]:
...     print(f"  [{suggestion['priority'].upper()}] {suggestion['file']}")
...     print(f"    {suggestion['suggestion']}")
```

### Test Generation Example

```python
>>> from apps.realtime_poc.features.testing import TestGenerator
>>>
>>> generator = TestGenerator()
>>>
>>> # Generate Python test
>>> result = generator.generate_python_test(
...     test_description="Test that divide function raises error for division by zero",
...     target_file="backend/calculator.py",
...     target_function="divide"
... )
>>>
>>> print("Generated Test:")
>>> print(result['test_code'])
```

### What It Does

- **Natural Language to Test**: Converts plain English descriptions to pytest/Jest test code
- **Test Type Detection**: Automatically identifies unit, integration, or E2E tests
- **Arrange-Act-Assert**: Generates proper test structure with setup, execution, and assertions
- **Test Execution**: Runs tests and parses results (passed, failed, output)
- **Coverage Analysis**: Identifies coverage gaps and suggests missing tests
- **Multi-Framework**: Supports Python (pytest) and JavaScript (Jest)

---

## Feature 8: Agent Memory & Learning System (v2.2)

### Quick Test

```python
>>> from apps.realtime_poc.features.memory import LearningSession
>>>
>>> # Initialize session
>>> session = LearningSession()
>>>
>>> # Record interactions
>>> for i in range(5):
...     session.record_interaction(
...         agent_name="test_agent",
...         task_type="implement_feature",
...         task_description=f"Feature {i}",
...         approach="TDD approach",
...         outcome="Success",
...         success=True,
...         duration_seconds=30.0 + i,
...         tags=["feature", "tdd"]
...     )
>>>
>>> # Learn patterns
>>> patterns = session.learn_patterns(min_occurrences=3)
>>> print(f"Learned {len(patterns)} patterns")
>>>
>>> # Get recommendations
>>> recs = session.get_recommendations("implement_feature")
>>> print(f"Recommendations: {len(recs['pattern_recommendations'])}")
>>> for rec in recs['pattern_recommendations']:
...     print(f"  - {rec['recommendation']}")
>>>
>>> # Add knowledge
>>> knowledge_id = session.add_knowledge(
...     category="testing",
...     title="TDD Best Practices",
...     content="Write tests first, then implement",
...     tags=["tdd", "testing"]
... )
>>>
>>> # Search knowledge
>>> results = session.search_knowledge("TDD")
>>> print(f"Found {len(results)} knowledge entries")
>>>
>>> # Get session stats
>>> stats = session.get_session_stats()
>>> print(f"Success rate: {stats['success_rate']}%")
>>> print(f"Patterns learned: {stats['patterns_learned']}")
```

### What It Does

- **Records Interactions**: Stores every agent task with approach, outcome, duration
- **Learns Patterns**: Identifies successful approaches, common failures, duration patterns
- **Builds Knowledge**: Creates searchable knowledge base from successful interactions
- **Provides Recommendations**: Suggests approaches based on historical success
- **Tracks Performance**: Monitors improvement over time through success rates
- **Enables Search**: Query past solutions and learned knowledge

---

## Feature 9: Cross-Repository Agent Orchestration (v2.2)

### Quick Test

```python
>>> from apps.realtime_poc.features.cross_repo import CrossRepoSession
>>> import tempfile
>>> import os
>>>
>>> # Create test directories
>>> with tempfile.TemporaryDirectory() as tmpdir:
...     repo1_path = os.path.join(tmpdir, "repo1")
...     repo2_path = os.path.join(tmpdir, "repo2")
...     os.makedirs(repo1_path)
...     os.makedirs(repo2_path)
...
...     # Initialize session
...     session = CrossRepoSession()
...
...     # Register repositories
...     repos = session.register_repositories([
...         {"name": "frontend", "path": repo1_path},
...         {"name": "backend", "path": repo2_path}
...     ])
...     print(f"Registered {len(repos)} repositories")
...
...     # Create workflow
...     workflow = session.create_workflow(
...         workflow_name="Update Authentication",
...         tasks=[
...             {
...                 "name": "Update Backend API",
...                 "description": "Add new auth endpoints",
...                 "repositories": ["backend"],
...                 "dependencies": []
...             },
...             {
...                 "name": "Update Frontend UI",
...                 "description": "Add login form",
...                 "repositories": ["frontend"],
...                 "dependencies": ["Update Backend API"]
...             }
...         ]
...     )
...
...     print(f"Created {workflow['tasks_created']} tasks")
...     print(f"Execution plan: {len(workflow['execution_plan'])} levels")
...
...     # Get status
...     status = session.get_session_status()
...     print(f"Total tasks: {status['total_tasks']}")
...     print(f"Status: {status['status_breakdown']}")
```

### What It Does

- **Manages Repositories**: Centralized registry of all repositories with status tracking
- **Coordinates Tasks**: Execute tasks across repos with dependency management
- **Resolves Dependencies**: Topological sort ensures correct execution order
- **Synchronizes State**: Keep repos in sync with remote branches
- **Assigns Agents**: Route tasks to appropriate agents per repository
- **Tracks Progress**: Monitor multi-repo workflow execution

---

## Feature 10: Session Persistence & Recovery System (v2.3)

### Quick Test

```python
>>> from apps.realtime_poc.features.session_persistence import SessionManager, MessageRole
>>>
>>> # Initialize manager
>>> manager = SessionManager()
>>>
>>> # Start new session
>>> session = manager.start_session(
...     title="Test Session",
...     description="Testing session persistence"
... )
>>> print(f"Session started: {session.id}")
>>>
>>> # Add messages
>>> manager.add_message(MessageRole.USER, "Hello, how are you?")
>>> manager.add_message(MessageRole.ASSISTANT, "I'm doing well, thank you!")
>>> manager.add_message(MessageRole.USER, "Can you help me with Python?")
>>>
>>> # Get conversation history
>>> history = manager.get_session_history(session.id)
>>> print(f"Messages in session: {len(history)}")
>>> for msg in history:
...     print(f"[{msg.role.value}] {msg.content[:30]}...")
>>>
>>> # Create checkpoint
>>> checkpoint = manager.create_checkpoint(
...     description="After initial greeting",
...     agent_states=[],
...     system_state={"messages": 3}
... )
>>> print(f"Checkpoint created: {checkpoint.description}")
>>>
>>> # List all sessions
>>> sessions = manager.list_sessions(limit=5)
>>> print(f"Total sessions: {len(sessions)}")
>>>
>>> # Export session
>>> path = manager.export_current_session(format="json")
>>> print(f"Session exported to: {path}")
>>>
>>> # End session
>>> manager.end_session()
>>> print("Session ended")
```

### What It Does

- **Persists Conversations**: Automatically saves all messages to SQLite database
- **Enables Resume**: Continue interrupted sessions from where you left off
- **Crash Recovery**: Detects crashed sessions and enables recovery
- **Snapshots**: Create point-in-time snapshots (auto and manual)
- **Rollback**: Restore session to previous checkpoint
- **Export/Import**: Share and archive sessions as JSON files
- **Session Search**: Find past conversations by status, date, or content

---

## Feature 11: Plugin System & Custom Tools (v2.3)

### Quick Test

```python
>>> from apps.realtime_poc.features.plugin_system import (
...     Plugin, PluginManager, PluginMetadata,
...     ToolDefinition, ToolParameter, ToolParameterType
... )
>>> from pathlib import Path
>>>
>>> # Create a simple test plugin
>>> class GreetingPlugin(Plugin):
...     def get_metadata(self):
...         return PluginMetadata(
...             id="greeting-plugin",
...             name="Greeting Plugin",
...             version="1.0.0",
...             description="Simple greeting tool",
...             author="Test User"
...         )
...
...     def get_tools(self):
...         return [
...             ToolDefinition(
...                 name="greet",
...                 description="Generate a greeting",
...                 parameters=[
...                     ToolParameter(
...                         name="name",
...                         type=ToolParameterType.STRING,
...                         description="Name to greet",
...                         required=True
...                     ),
...                     ToolParameter(
...                         name="formal",
...                         type=ToolParameterType.BOOLEAN,
...                         description="Use formal greeting",
...                         required=False,
...                         default=False
...                     )
...                 ],
...                 returns="Greeting message"
...             )
...         ]
...
...     def execute_tool(self, tool_name, parameters):
...         if tool_name == "greet":
...             name = parameters["name"]
...             formal = parameters.get("formal", False)
...             if formal:
...                 return f"Good day, {name}."
...             return f"Hey {name}!"
>>>
>>> # Test plugin directly
>>> plugin = GreetingPlugin()
>>> metadata = plugin.get_metadata()
>>> print(f"Plugin: {metadata.name} v{metadata.version}")
>>>
>>> tools = plugin.get_tools()
>>> print(f"Tools: {[t.name for t in tools]}")
>>>
>>> # Execute tool
>>> result = plugin.execute_tool("greet", {"name": "Alice", "formal": True})
>>> print(f"Result: {result}")
>>>
>>> result = plugin.execute_tool("greet", {"name": "Bob"})
>>> print(f"Result: {result}")
>>>
>>> # Test with PluginManager (using built-in example)
>>> from apps.realtime_poc.features.plugin_system import ExamplePlugin
>>> manager = PluginManager()
>>>
>>> # Manually add example plugin
>>> example = ExamplePlugin()
>>> metadata = example.get_metadata()
>>> manager.loaded_plugins[metadata.id] = example
>>> plugin_info = manager.registry.register_plugin(metadata.id, metadata)
>>> manager.enable_plugin(metadata.id)
>>>
>>> # Execute example tool
>>> result = manager.execute_tool(
...     "example-plugin",
...     "example_tool",
...     {"message": "hello world", "uppercase": True}
... )
>>> print(f"Tool result: {result}")
>>>
>>> # List plugins
>>> plugins = manager.list_plugins()
>>> print(f"Installed plugins: {len(plugins)}")
```

### What It Does

- **Extensibility**: Add custom tools without modifying core code
- **Plugin Discovery**: Auto-load plugins from `plugins/installed` directory
- **Tool Definitions**: Define tools with typed parameters and schemas
- **Lifecycle Management**: Install, enable, disable, uninstall plugins
- **OpenAI Integration**: Export plugin tools as OpenAI function definitions
- **Configuration**: Per-plugin configuration (API keys, settings)
- **Templates**: Quick-start templates for creating new plugins

---

## Integration with Voice Agent

All features are designed to integrate with the main voice agent. See `docs/IMPLEMENTATION_GUIDE.md` for complete integration instructions.

### Example Voice Commands (once integrated)

**Collaboration Rooms**:
- "Create collaboration room for user authentication"
- "Add backend-dev agent to the room"
- "Assign task to room: implement login endpoint"

**Macros**:
- "Run macro test-and-commit"
- "List available macros"
- "Execute video-generation macro with prompt 'sunset over mountains'"

**Analytics**:
- "Show me analytics for this week"
- "What's my cost today?"
- "Get optimization recommendations"

**Code Review**:
- "Review the backend code for security issues"
- "Show me performance problems"
- "Apply this fix"

**Git Assistant**:
- "Commit my changes with an AI message"
- "Create a pull request"
- "Resolve merge conflicts"

**Debugging Assistant** (v2.1):
- "Analyze this error: [paste error text]"
- "Debug the AttributeError in app.py"
- "Check the logs for database errors"
- "Suggest a fix for this KeyError"
- "Where should I set breakpoints?"

**Testing Framework** (v2.1):
- "Generate tests for the authentication module"
- "Create a test that validates email format"
- "Run all tests"
- "Show me test coverage"
- "Which files need more tests?"

**Agent Memory & Learning** (v2.2):
- "What's the best way to implement authentication?"
- "Remember this approach for database tasks"
- "Search knowledge for JWT security"
- "How am I performing?"
- "Learn patterns from recent tasks"

**Cross-Repository Orchestration** (v2.2):
- "Register repository myapp-frontend at /path/to/repo"
- "Create workflow to update auth in backend and frontend"
- "Execute next available tasks"
- "Sync all repositories"
- "Show workflow status"

**Session Persistence & Recovery** (v2.3):
- "Save checkpoint with description 'completed user auth feature'"
- "List my checkpoints"
- "Roll back to checkpoint [checkpoint-id]"
- "Export this session"
- "Resume session [session-id]"
- "Show my recent sessions"

**Plugin System & Custom Tools** (v2.3):
- "List available plugins"
- "Enable the weather plugin"
- "Disable the database plugin"
- "Get weather for San Francisco" (uses plugin tool)
- "Show tools from slack-plugin"

---

## Directory Structure After Using Features

```
big-3-super-agent/
├── .claude/
│   └── macros/               # Your macro definitions
│       ├── hello-world.yaml
│       └── ...
│
├── analytics/
│   └── metrics.db            # Performance metrics database
│
├── apps/content-gen/
│   └── agents/
│       ├── claude_code/
│       ├── gemini/
│       └── collaboration_rooms/  # Room data
│           ├── registry.json
│           └── [room-name]/
│               ├── operator_log.md
│               ├── screenshots/
│               └── final_state.json (when archived)
│
├── sessions/                   # Session persistence data (v2.3)
│   ├── session_store.db        # SQLite database for sessions
│   ├── recovery/               # Recovery points
│   └── exports/                # Exported sessions
│
├── plugins/                    # Plugin system (v2.3)
│   ├── installed/              # Installed plugins
│   │   ├── weather_plugin.py
│   │   └── ...
│   └── registry.json           # Plugin metadata
│
└── apps/realtime-poc/
    └── features/             # Feature implementations
        ├── __init__.py
        ├── collaboration_rooms.py (v2.0)
        ├── macros.py (v2.0)
        ├── analytics.py (v2.0)
        ├── code_review.py (v2.0)
        ├── git_assistant.py (v2.0)
        ├── debugging.py (v2.1)
        ├── testing.py (v2.1)
        ├── memory.py (v2.2)
        ├── cross_repo.py (v2.2)
        ├── session_persistence.py (v2.3)
        └── plugin_system.py (v2.3)
```

---

## Troubleshooting

### "Module not found" errors

Make sure you're running Python from the project root:
```bash
cd /home/user/big-3-super-agent
python3
```

### "Database locked" errors (Analytics)

The SQLite database doesn't support high concurrency. For production, use PostgreSQL.

### "File not found" errors (Collaboration Rooms)

The base directory defaults to `apps/content-gen`. Ensure it exists:
```bash
ls apps/content-gen
```

### Macro execution fails

Check:
1. YAML syntax is correct
2. All required parameters are provided
3. Action handlers are registered for custom actions

---

## Next Steps

1. **Read Full Documentation**: See `docs/IMPLEMENTATION_GUIDE.md`
2. **Review Feature Specs**: Check `docs/features/` for detailed specifications
3. **Try Examples**: Test each feature independently before integration
4. **Create Custom Macros**: Build workflows specific to your needs
5. **Monitor Analytics**: Track your agent usage and optimize costs

---

## Support

For issues or questions:
1. Check the implementation guide: `docs/IMPLEMENTATION_GUIDE.md`
2. Review feature documentation: `docs/features/`
3. Examine the code: `apps/realtime-poc/features/`

All eleven features (v2.0-v2.3) are production-ready and fully documented!
