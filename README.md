# Big Three Realtime Agents
> Voice agent (OpenAI Realtime API) that orchestrates coding agents (Claude Code) and browser agents (Gemini Computer Use)
> 
> **See this codebase in action [here](https://youtu.be/Ur3TJm0BckQ)**
> 

<img src="images/big-3-super-agent.png" alt="Big Three Super Agent" style="max-width: 800px; width: 100%;">

A unified voice-controlled orchestrator that coordinates three types of AI agents:
1. **OpenAI Realtime Voice Agent** - Natural voice interactions and orchestration
2. **Claude Code Agentic Coder** - Software development and file operations
3. **Gemini Browser Agent** - Web automation and validation

## 🎯 New Features (v2.0)

This release adds five powerful features that transform the system into a comprehensive AI-powered development platform:

1. **🤝 Multi-Agent Collaboration Rooms** - Multiple agents working together in shared workspaces with coordinated task execution
2. **⚡ Voice Command Macros** - Execute complex multi-step workflows with a single voice command
3. **📊 Performance Analytics & Dashboard** - Comprehensive metrics, cost tracking, and AI-powered optimization recommendations
4. **🔍 Interactive Voice Code Review** - Natural language code reviews with multi-dimensional analysis (security, performance, style)
5. **🔄 Intelligent Git Assistant** - Voice-controlled git operations with AI-generated commit messages and PR descriptions

## 🚀 Phase 1 Features (v2.1)

Building on v2.0, Phase 1 adds two high-value features focused on developer productivity:

6. **🐛 Voice-Activated Debugging Assistant** - Analyzes errors, stack traces, and logs to provide intelligent debugging assistance with automated fix suggestions
7. **🧪 Natural Language Testing Framework** - Generate and execute tests from plain English descriptions with automated coverage analysis

## 🎓 Phase 2 Features (v2.2)

Phase 2 introduces intelligent learning and multi-repository capabilities:

8. **🧠 Agent Memory & Learning System** - Tracks interactions, learns from patterns, builds searchable knowledge base for continuous improvement
9. **🔗 Cross-Repository Agent Orchestration** - Coordinates agents across multiple repositories with dependency resolution and workflow automation

## 📦 Phase 3 Features (v2.3)

Phase 3 adds session management and extensibility:

10. **💾 Session Persistence & Recovery System** - Automatic conversation history persistence, session resume, crash recovery, and rollback capabilities
11. **🔌 Plugin System & Custom Tools** - Extensibility framework for creating custom agent tools and integrating third-party services

See [IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md) for detailed usage and integration instructions.

## Requirements

- **Python 3.11+**
- **[Astral uv](https://docs.astral.sh/uv/)** - Fast Python package installer and runner
- **API Keys**: OpenAI, Anthropic (Claude), Google (Gemini)
- **Playwright**: For browser automation (`playwright install` after setup)

Install `uv` if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

### 1. Clone and Navigate
```bash
cd apps/realtime-poc
```

### 2. Configure Environment
Copy `.env.sample` to `.env` and fill in required values:

```bash
# Required API Keys
OPENAI_API_KEY=sk-...           # For voice orchestration
ANTHROPIC_API_KEY=sk-ant-...    # For Claude Code agents
GEMINI_API_KEY=...              # For browser automation

# Optional API Keys (for future extensibility)
GROQ_API_KEY=
DEEPSEEK_API_KEY=
ELEVENLABS_API_KEY=             # For advanced TTS

# Configuration
ENGINEER_NAME=Dan               # Your name (for agent interactions)
AGENT_WORKING_DIRECTORY=        # Leave empty to use default (apps/content-gen)
```

### 3. Install Playwright
```bash
playwright install
```

### 4. Run
```bash
# Voice mode (recommended for full experience)
uv run big_three_realtime_agents.py --voice

# Text mode (for testing)
uv run big_three_realtime_agents.py --input text --output text

# Auto-dispatch with prompt
uv run big_three_realtime_agents.py --prompt "Create a new claude code agent, and have it list all the files in the working directory"

# Use mini model (faster/cheaper)
uv run big_three_realtime_agents.py --mini --voice
```

## Architecture

```mermaid
graph TD
    User[User Voice/Text Input] --> OAI[OpenAI Realtime Voice Agent]

    OAI -->|Create Agent| CREATE[create_agent Tool]
    OAI -->|Send Instructions| CMD[command_agent Tool]
    OAI -->|Query Status| LIST[list_agents Tool]
    OAI -->|Direct Browser| BU[browser_use Tool]
    OAI -->|File Access| RF[read_file/open_file]

    CREATE -->|Claude Code| CC[Claude Code Agent]
    CREATE -->|Gemini| GB[Gemini Browser Agent]
    CMD -->|Instructions| CC
    CMD -->|Instructions| GB

    CC -->|Write Code| WD[Working Directory: apps/content-gen]
    CC -->|Store Sessions| REG1[Registry: agents/claude_code/]

    GB -->|Browse/Validate| BR[Playwright Browser]
    GB -->|Store Sessions| REG2[Registry: agents/gemini/]
    BU -->|Direct Control| BR

    BR -->|Screenshots| SS[output_logs/screenshots/]

    WD -->|Agents Work Here| FS[Backend/Frontend Code]

    OAI -->|Response| User

    style OAI fill:#ff9,stroke:#333
    style CC fill:#9cf,stroke:#333
    style GB fill:#c9f,stroke:#333
    style WD fill:#9f9,stroke:#333
```

## Key Directories & Files

### Project Structure
```
big-3-super-agent/
├── .env.sample                 # Environment template
├── docs/                      # Comprehensive documentation
│   ├── CODEBASE_DOCUMENTATION.md    # Full system documentation
│   ├── FEATURE_PROPOSALS.md         # Feature overview
│   ├── IMPLEMENTATION_GUIDE.md      # Implementation & usage guide
│   ├── QUICK_START_NEW_FEATURES.md  # Quick start for all features
│   └── features/                    # Detailed feature docs
│       ├── 01-multi-agent-collaboration-rooms.md (v2.0)
│       ├── 02-voice-command-macros.md (v2.0)
│       ├── 03-agent-performance-analytics.md (v2.0)
│       ├── 04-interactive-voice-code-review.md (v2.0)
│       ├── 05-intelligent-version-control-assistant.md (v2.0)
│       ├── 06-debugging-assistant.md (v2.1)
│       ├── 07-testing-framework.md (v2.1)
│       ├── 08-agent-memory-learning.md (v2.2)
│       ├── 09-cross-repository-orchestration.md (v2.2)
│       ├── 10-session-persistence-recovery.md (v2.3)
│       └── 11-plugin-system-custom-tools.md (v2.3)
├── apps/
│   ├── content-gen/           # Agent working directory (default - you can change this to any directory you want)
│   │   ├── agents/            # Agent session registries
│   │   │   ├── claude_code/   # Claude Code agent sessions
│   │   │   ├── gemini/        # Gemini agent sessions
│   │   │   └── collaboration_rooms/  # Multi-agent rooms
│   │   ├── backend/           # Backend code (agents work here)
│   │   ├── frontend/          # Frontend code (agents work here)
│   │   ├── specs/             # Project specifications
│   │   └── logs/              # Agent execution logs
│   └── realtime-poc/          # Main orchestrator
│       ├── big_three_realtime_agents.py  # Main entry point
│       ├── features/          # New feature modules (v2.0 + v2.1 + v2.2 + v2.3)
│       │   ├── collaboration_rooms.py   # Multi-agent coordination (v2.0)
│       │   ├── macros.py                # Workflow automation (v2.0)
│       │   ├── analytics.py             # Performance metrics (v2.0)
│       │   ├── code_review.py           # Code analysis (v2.0)
│       │   ├── git_assistant.py         # Git operations (v2.0)
│       │   ├── debugging.py             # Debugging assistant (v2.1)
│       │   ├── testing.py               # Testing framework (v2.1)
│       │   ├── memory.py                # Agent memory & learning (v2.2)
│       │   ├── cross_repo.py            # Cross-repo orchestration (v2.2)
│       │   ├── session_persistence.py   # Session persistence & recovery (v2.3)
│       │   └── plugin_system.py         # Plugin system & custom tools (v2.3)
│       ├── prompts/           # System prompts for agents
│       │   └── super_agent/   # Orchestrator prompts
│       └── output_logs/       # Voice agent logs & screenshots
├── .claude/
│   ├── macros/                # Voice command macros (YAML)
│   └── hooks/                 # Observability hooks
└── analytics/                 # Performance metrics database
```

### Important Files

- **`big_three_realtime_agents.py`**: Main orchestrator script (3000+ lines)
  - Line 184-616: `GeminiBrowserAgent` class
  - Line 617-1540: `ClaudeCodeAgenticCoder` class
  - Line 1541-2900: `OpenAIRealtimeVoiceAgent` class

- **Working Directory**: `apps/content-gen/` (configurable via `AGENT_WORKING_DIRECTORY`)
  - All Claude Code agents operate with this as their `cwd`
  - Agents create/modify files relative to this directory
  - Registries stored in `agents/` subdirectory

## How It Works

### 1. Voice Orchestration
The OpenAI Realtime Voice Agent acts as the main orchestrator:
- Listens to user voice/text input
- Decides which agent type to use
- Dispatches tasks via tool calls
- Manages agent lifecycle (create, resume, list, delete)

### 2. Agent Working Directory
Agents are pointed to a specific working directory:
```python
AGENT_WORKING_DIRECTORY = Path(__file__).parent.parent / "content-gen"
```

- **Claude Code agents**: Work in this directory with full file access
- **Gemini agents**: Store browser session data here
- **Registries**: Each agent type has a registry file tracking active sessions

### 3. Tool-Based Dispatch
The orchestrator exposes these tools to the voice agent:
- `list_agents()` - Query all active agents and their status
- `create_agent(tool, type, agent_name)` - Create a new agent (Claude Code or Gemini)
- `command_agent(agent_name, prompt)` - Send instructions to an existing agent
- `delete_agent(agent_name)` - Remove an agent session
- `check_agent_result(agent_name, operator_file_name)` - Check agent execution results
- `browser_use(task, url)` - Direct browser automation task
- `open_file(file_path)` - Open a file in the default application
- `read_file(file_path)` - Read file contents
- `report_costs()` - Get API usage and cost information

### 4. Session Management
- Each agent gets a unique session ID
- Sessions stored in registry JSON files
- Sessions can be resumed across voice interactions
- Operator files created for each coding task

## Multi Agent Observability

This project includes built-in observability for tracking all agent activities in real-time. The system uses [Claude Code Hooks Multi-Agent Observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) to stream events from all agents to a centralized dashboard.

### How It Works

**Zero setup required** - just turn it on and agents automatically ping out events:

1. **Claude Code Hooks** (`.claude/settings.json`): Automatically triggered on tool use, notifications, session stops, etc.
2. **Send Event Hook** (`.claude/hooks/send_event.py`): Forwards hook events to the observability server with AI-generated summaries
3. **OpenAI Agent Integration**: The `_send_observability_event` tool in `big_three_realtime_agents.py` sends custom events from the voice orchestrator

### What You See

- **Real-time event stream**: Every tool call, agent creation, file operation, and browser action
- **AI-generated summaries**: Automatic context-aware descriptions of what's happening
- **Session tracking**: Follow multiple agent sessions across the entire lifecycle
- **Cost monitoring**: Track API usage via the `report_costs()` tool
- **Chat transcripts**: Full conversation history included on session stops

### Quick Start

1. Clone and run the observability server:
   ```bash
   git clone https://github.com/disler/claude-code-hooks-multi-agent-observability
   cd claude-code-hooks-multi-agent-observability
   npm install && npm run dev
   ```

2. Start the agents (observability is already configured):
   ```bash
   uv run big_three_realtime_agents.py --voice
   ```

3. Open the dashboard at `http://localhost:3000`

Events automatically flow from:
- Claude Code agent tool calls (PreToolUse, PostToolUse)
- Voice orchestrator decisions
- Gemini browser actions
- Session lifecycle events

No configuration needed - it just works!

## Built With

This project is powered by cutting-edge AI technologies:

- **[Gemini 2.5 Computer Use](https://blog.google/technology/google-deepmind/gemini-computer-use-model/)** - Browser automation with vision and action planning
- **[OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)** - Natural voice interactions and orchestration
- **[OpenAI Sora API](https://platform.openai.com/docs/guides/video-generation)** - Video generation capabilities
- **[Claude Code](https://claude.com/product/claude-code)** - Agentic software development
- **[Astral uv](https://docs.astral.sh/uv/)** - Fast Python package management and script execution
- **[Tactical Agentic Coding](https://agenticengineer.com/tactical-agentic-coding)** - Agentic coding patterns and best practices

## ✅ Implemented Features

**v2.0 (5 features)**:
- **✅ Multi-agent coordination**: Collaboration rooms enable multiple agents to work together with shared context
- **✅ Workflow automation**: Voice macros allow complex multi-step workflows with single commands
- **✅ Cost tracking**: Comprehensive analytics with cost breakdown by agent, task type, and project
- **✅ Code quality**: Interactive voice code review with security, performance, and style analysis
- **✅ Git integration**: Intelligent git assistant with AI-powered commit messages and PR descriptions

**v2.1 Phase 1 (2 features)**:
- **✅ Debugging assistance**: Voice-activated debugging with error analysis, fix suggestions, and log analysis
- **✅ Test automation**: Natural language test generation with coverage analysis and gap identification

**v2.2 Phase 2 (2 features)**:
- **✅ Agent learning**: Memory system tracks interactions, learns patterns, builds searchable knowledge base
- **✅ Multi-repo orchestration**: Coordinates agents across multiple repositories with dependency resolution

**v2.3 Phase 3 (2 features)**:
- **✅ Session management**: Automatic conversation history persistence, session resume, and crash recovery
- **✅ Plugin system**: Extensibility framework for custom tools and third-party integrations

**Infrastructure**:
- **✅ Modular architecture**: Features implemented as separate modules in `apps/realtime-poc/features/`
- **✅ Zero doc debt**: Complete documentation for codebase and all features

## Future Improvements

- **Break up main file**: Refactor `big_three_realtime_agents.py` to use feature modules
- **Error handling**: Add better recovery from API failures with retry logic
- **Session persistence**: Store voice conversation history across sessions
- **Agent isolation**: Sandbox agent file operations more strictly
- **Better logging**: Structured logging with trace IDs
- **Testing**: Add comprehensive unit tests for each feature
- **Configuration**: Move remaining hardcoded values to config file
- **Agent interruption**: Enable agents to be interrupted and redirected mid-task
- **Web dashboard**: Build web UI for analytics and monitoring (currently terminal-based)

## Future Directions

- **Multi-modal input**: Support image/video inputs for richer context
- **Agent templates**: Pre-configured agent profiles for common tasks
- **Tool extensions**: Plugin system for custom agent tools
- **Collaborative coding**: Multiple engineers working with same agents
- **Browser recording**: Record agent actions for debugging
- **Voice customization**: Train custom voice models
- **Mobile support**: iOS/Android companion apps
- **Cloud deployment**: Containerized deployment with Redis for state
- **Agent marketplace**: Share and discover agent configurations

## Troubleshooting

**"OPENAI_API_KEY not set"**: Ensure `.env` file exists and contains valid API key

**"playwright not found"**: Run `playwright install` after initial setup

**Agents not working in correct directory**: Check `AGENT_WORKING_DIRECTORY` in `.env`

**Voice not working**: Ensure microphone permissions granted and `pyaudio` installed

---

## Master AI **Agentic Coding**
> And prepare for the future of software engineering

Learn tactical agentic coding patterns with [Tactical Agentic Coding](https://agenticengineer.com/tactical-agentic-coding)

Follow the [IndyDevDan YouTube channel](https://www.youtube.com/@indydevdan) to improve your agentic coding advantage.

