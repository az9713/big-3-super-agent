# Big Three Realtime Agents - Comprehensive Codebase Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [System Components](#system-components)
5. [Agent Systems](#agent-systems)
6. [Content-Gen Demo Application](#content-gen-demo-application)
7. [Observability & Hooks](#observability--hooks)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Development Workflows](#development-workflows)
11. [Design Patterns](#design-patterns)
12. [Data Flow](#data-flow)

---

## Overview

### What is Big Three Realtime Agents?

Big Three Realtime Agents is a **voice-controlled multi-agent orchestration system** that combines three cutting-edge AI technologies to enable natural language control over software development and web automation tasks. The system allows users to speak to an AI orchestrator that intelligently delegates work to specialized agents.

### The Three Agents

1. **OpenAI Realtime Voice Agent** - Main orchestrator handling voice/text interactions
2. **Claude Code Agentic Coder** - Software development specialist (reading, writing, editing code)
3. **Gemini Browser Agent** - Web automation and validation using computer vision

### Demo Application

The project includes **Content-Gen**, a full-stack video generation application using OpenAI's Sora API. This serves as both a testing ground and working example of agent collaboration.

### Key Capabilities

- **Voice Control**: Natural language commands for development tasks
- **Multi-Agent Coordination**: Orchestrator delegates to specialized agents
- **Code Development**: Full-featured code editing, file operations, testing
- **Web Automation**: Vision-based browser control and validation
- **Video Generation**: Integration with OpenAI Sora for AI video creation
- **Session Persistence**: Resume agents and tasks across sessions
- **Real-time Observability**: Event streaming and monitoring

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│            (Voice Input / Text Commands)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          OpenAI Realtime Voice Agent (Orchestrator)         │
│  • WebSocket connection to OpenAI Realtime API             │
│  • Voice/text processing (24kHz PCM audio)                 │
│  • Tool dispatch and coordination                          │
│  • Cost tracking and analytics                             │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────────┐  ┌───────────────────────────┐
│  ClaudeCodeAgenticCoder    │  │   GeminiBrowserAgent      │
│  • Code generation/editing │  │   • Web automation        │
│  • File operations         │  │   • Screenshot capture    │
│  • Testing & validation    │  │   • Vision-based control  │
│  • Operator logs           │  │   • Action execution      │
│  • Session registry        │  │   • Session tracking      │
└────────────┬───────────────┘  └───────────┬───────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────────────────────────────────────────┐
│                   Working Directory                         │
│              apps/content-gen/                              │
│   ┌──────────────┐         ┌──────────────┐               │
│   │   Backend    │◄────────┤   Frontend   │               │
│   │  (FastAPI)   │         │   (Vue 3)    │               │
│   └──────┬───────┘         └──────────────┘               │
│          │                                                  │
│          ▼                                                  │
│   ┌──────────────────┐                                     │
│   │  OpenAI Sora API │                                     │
│   │ Video Generation │                                     │
│   └──────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Observability System (.claude/hooks/)          │
│  • Event streaming to monitoring dashboard                 │
│  • AI-powered event summarization                          │
│  • Text-to-speech notifications                            │
│  • Session tracking and chat transcripts                   │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
/home/user/big-3-super-agent/
│
├── apps/
│   ├── realtime-poc/                    # Main orchestrator
│   │   ├── big_three_realtime_agents.py # 3228 lines - all agent classes
│   │   ├── prompts/super_agent/         # System prompts
│   │   │   ├── create_agent.md
│   │   │   ├── command_agent.md
│   │   │   ├── check_agent_result.md
│   │   │   └── delete_agent.md
│   │   └── pyproject.toml
│   │
│   └── content-gen/                     # Agent working directory
│       ├── backend/                     # FastAPI application
│       │   ├── src/content_gen_backend/
│       │   │   ├── main.py              # FastAPI app setup
│       │   │   ├── config.py            # Configuration
│       │   │   ├── routers/
│       │   │   │   └── videos.py        # Video API endpoints
│       │   │   ├── services/
│       │   │   │   ├── sora_service.py  # Sora API wrapper
│       │   │   │   └── storage_service.py # File storage
│       │   │   └── models/              # Pydantic schemas
│       │   │       ├── request.py
│       │   │       ├── response.py
│       │   │       └── video.py
│       │   ├── videos/                  # Video storage
│       │   └── pyproject.toml
│       │
│       ├── frontend/                    # Vue 3 SPA
│       │   ├── src/
│       │   │   ├── App.vue              # Main component
│       │   │   ├── components/
│       │   │   │   ├── VideoCreator.vue
│       │   │   │   ├── VideoProgress.vue
│       │   │   │   ├── VideoLibrary.vue
│       │   │   │   └── VideoPlayer.vue
│       │   │   ├── composables/
│       │   │   │   ├── useVideoGeneration.ts
│       │   │   │   └── useVideoLibrary.ts
│       │   │   └── types/video.ts
│       │   ├── package.json
│       │   └── vite.config.ts
│       │
│       ├── agents/                      # Session data
│       │   ├── claude_code/
│       │   │   └── registry.json        # Active Claude sessions
│       │   └── gemini/
│       │       └── registry.json        # Active Gemini sessions
│       │
│       ├── specs/                       # Implementation plans
│       │   └── sora-video-generation-integration.md
│       │
│       └── .claude/                     # Project commands
│           └── commands/
│
├── .claude/                             # Global Claude hooks
│   ├── settings.json                    # Hook configuration
│   ├── hooks/                           # Event handlers
│   │   ├── send_event.py               # Observability integration
│   │   ├── pre_tool_use.py             # Pre-tool execution
│   │   ├── post_tool_use.py            # Post-tool execution
│   │   ├── notification.py             # User notifications
│   │   ├── stop.py                     # Session end handler
│   │   └── utils/
│   │       ├── summarizer.py           # AI summarization
│   │       ├── tts/                    # Text-to-speech
│   │       │   ├── openai_tts.py
│   │       │   ├── elevenlabs_tts.py
│   │       │   └── pyttsx3_tts.py
│   │       └── llm/                    # LLM clients
│   │           ├── anthropic_client.py
│   │           └── openai_client.py
│   │
│   └── commands/                        # Custom slash commands
│       ├── quick-plan.md               # Generate implementation plans
│       ├── build.md                    # Build from plan
│       ├── question.md                 # Answer questions
│       ├── load_ai_docs.md             # Fetch documentation
│       └── reset_content_gen.md        # Reset demo app
│
├── logs/                                # Session logs
├── output_screenshots/                  # Browser screenshots
└── docs/                                # Documentation (this file)
```

---

## Technology Stack

### Core Orchestrator (`apps/realtime-poc/`)

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Main language | 3.11+ |
| uv | Package manager | Latest |
| OpenAI Realtime API | Voice interaction | WebSocket |
| Claude Agent SDK | Code agent management | Latest |
| Google Gemini 2.5 | Computer use API | Latest |
| Playwright | Browser automation | Latest |
| PyAudio | Audio I/O | Latest |
| NumPy | Audio processing | Latest |
| Rich | Terminal UI | Latest |
| WebSockets | Real-time communication | Latest |

### Backend (`apps/content-gen/backend/`)

| Technology | Purpose | Version |
|------------|---------|---------|
| FastAPI | Web framework | Latest |
| Uvicorn | ASGI server | Latest |
| OpenAI Python SDK | Sora API client | Latest |
| Pydantic | Data validation | v2 |
| Python | Language | 3.11+ |

### Frontend (`apps/content-gen/frontend/`)

| Technology | Purpose | Version |
|------------|---------|---------|
| Vue | UI framework | 3.x |
| TypeScript | Type safety | Latest |
| Vite | Build tool | Latest |
| Axios | HTTP client | Latest |

### Observability (`/.claude/hooks/`)

| Technology | Purpose | Version |
|------------|---------|---------|
| Claude Haiku | Event summarization | Latest |
| OpenAI TTS | Text-to-speech | Latest |
| ElevenLabs | Premium TTS | Latest |
| pyttsx3 | Offline TTS | Latest |

---

## System Components

### 1. OpenAI Realtime Voice Agent

**File**: `apps/realtime-poc/big_three_realtime_agents.py` (Lines 1541-2900+)

#### Purpose
Main orchestrator that handles user interaction and delegates work to specialized agents.

#### Key Responsibilities
- WebSocket communication with OpenAI Realtime API
- Voice input/output processing (24kHz PCM audio)
- Tool dispatch and coordination
- Agent lifecycle management (create, command, delete)
- Token usage and cost tracking
- Keyboard shortcuts (Shift+Space to pause audio)

#### Core Methods

##### `__init__()`
```python
def __init__(
    self,
    mode: str = "text",
    system_prompt: str | None = None,
    initial_prompt: str | None = None,
    auto_mode_timeout: int | None = None,
)
```
- Initializes voice agent with mode (text/voice-to-text/voice-to-voice)
- Sets up audio streams, WebSocket connection, system prompt
- Configures observability and cost tracking

##### `_build_tool_specs()`
```python
def _build_tool_specs(self) -> list[dict]
```
Returns tool specifications for the voice agent:
- `list_agents()` - Query active agents
- `create_agent()` - Spawn Claude/Gemini agent
- `command_agent()` - Send task to agent
- `check_agent_result()` - Read operator logs
- `delete_agent()` - Remove agent session
- `browser_use()` - Direct browser automation
- `read_file()` - Read file contents
- `open_file()` - Open in VS Code/default app
- `report_costs()` - Token/cost analysis

##### `_handle_function_call_delta()`
```python
def _handle_function_call_delta(self, delta: dict)
```
- Processes streaming function arguments
- Accumulates partial JSON
- Handles multi-turn function calls

##### `_handle_response_done()`
```python
def _handle_response_done(self, event: dict)
```
- Executes tools when response complete
- Delegates to appropriate handlers
- Sends results back to conversation

##### `run()`
```python
def run(self)
```
- Main event loop
- Handles keyboard input (Shift+Space)
- Processes WebSocket events
- Manages audio streaming
- Tracks latency metrics

#### Audio Control

| Control | Action |
|---------|--------|
| Shift+Space | Pause/resume microphone |
| Auto-pause | During agent speech |
| Beep (520Hz) | Microphone resumed |
| Beep (380Hz) | Microphone paused |

#### Modes

1. **Text-to-Text**: Terminal input/output only
2. **Voice-to-Text**: Voice input, text output
3. **Voice-to-Voice**: Full voice conversation

---

### 2. Claude Code Agentic Coder

**File**: `apps/realtime-poc/big_three_realtime_agents.py` (Lines 617-1540)

#### Purpose
Manages Claude Code agents for software development tasks.

#### Key Responsibilities
- Agent session registry management
- Operator log file creation and tracking
- Background thread execution for async tasks
- Browser tool injection for frontend validation
- Working directory isolation

#### Session Registry Structure

**Location**: `apps/content-gen/agents/claude_code/registry.json`

```json
{
  "agent_name": {
    "agent_name": "nova",
    "session_id": "uuid-here",
    "working_directory": "/home/user/big-3-super-agent/apps/content-gen",
    "operator_log_file": "/path/to/operator_log.md",
    "created_at": "2025-01-17T10:30:00",
    "last_command": "Add delete button to video library",
    "status": "active"
  }
}
```

#### Core Methods

##### `create_agent()`
```python
def create_agent(
    self,
    agent_name: str,
    type: str,
    agent_slug: str,
    working_directory: str | None = None,
) -> dict
```
- Initializes new coding agent with system prompt
- Creates session entry in registry
- Sets up working directory
- Returns agent metadata

##### `command_agent()`
```python
def command_agent(
    self,
    agent_name: str,
    prompt: str,
    agent_slug: str,
) -> dict
```
- Sends coding task to agent
- Generates operator log filename using Claude Opus
- Launches background thread for execution
- Returns task acknowledgment

##### `_create_browser_tool()`
```python
def _create_browser_tool(
    self,
    agent_name: str,
    screenshot_dir: str,
) -> dict
```
- Injects browser validation capability into Claude agents
- Allows Claude to use Gemini for UI testing
- Creates agent-specific screenshot directory

##### `check_agent_result()`
```python
def check_agent_result(
    self,
    agent_name: str,
    agent_slug: str,
) -> dict
```
- Retrieves operator log contents
- Returns agent status and results
- Shows progress and blockers

##### `delete_agent()`
```python
def delete_agent(
    self,
    agent_name: str,
    agent_slug: str,
) -> dict
```
- Removes agent from registry
- Cleans up resources
- Preserves operator logs for audit trail

#### Operator Log Pattern

Operator logs are markdown files that document each coding task:

**Filename Format**: Generated by Claude Opus based on task description
- Example: `add-delete-button-to-video-library-2025-01-17-103045.md`

**Content Structure**:
```markdown
# Task: [Description]

## Plan
- Step 1
- Step 2
- ...

## Progress
- [Timestamp] Started task
- [Timestamp] Completed step 1
- ...

## Blockers
- Issue encountered
- Resolution approach

## Results
- Files modified
- Tests run
- Validation performed

## Wrap-up
Final status and notes
```

#### System Prompt

Claude agents are instructed to be:
- **Scrappy**: Pragmatic over perfect
- **Staff Engineer**: Senior-level decision making
- **Non-perfectionist**: Ship functional code quickly
- **Thorough**: Test and validate work
- **Communicative**: Update operator logs frequently

---

### 3. Gemini Browser Agent

**File**: `apps/realtime-poc/big_three_realtime_agents.py` (Lines 184-616)

#### Purpose
Web automation using Gemini's computer vision and action planning.

#### Key Responsibilities
- Playwright browser control (Chromium, headless=False)
- Screenshot capture and management
- Action execution (click, type, scroll, navigate)
- Coordinate normalization (0-999 range to pixel coordinates)
- Session-based screenshot organization

#### Core Methods

##### `setup_browser()`
```python
async def setup_browser(self)
```
- Initializes Playwright
- Launches Chromium browser (headless=False)
- Creates new page
- Sets viewport to 1280x720

##### `execute_task()`
```python
async def execute_task(
    self,
    session_id: str,
    task_description: str,
) -> dict
```
- Main entry point for automation
- Creates screenshot directory
- Runs automation loop
- Returns results and screenshot paths

##### `_run_browser_automation_loop()`
```python
async def _run_browser_automation_loop(
    self,
    task_description: str,
    screenshot_dir: str,
    max_turns: int = 30,
) -> dict
```
- Gemini agent loop with vision feedback
- Takes screenshot after each action
- Sends to Gemini for next action planning
- Executes returned function calls
- Maximum 30 iterations per task

##### `_execute_gemini_function_calls()`
```python
async def _execute_gemini_function_calls(
    self,
    function_calls: list,
    screenshot_dir: str,
    turn: int,
) -> list[str]
```
- Executes browser actions from Gemini
- Maps coordinates to pixels
- Captures screenshots
- Returns screenshot paths

#### Browser Actions

| Action | Parameters | Description |
|--------|------------|-------------|
| `click` | `x: int, y: int` | Click at normalized coordinates (0-999) |
| `type` | `text: str` | Type text at focused element |
| `scroll_down` | - | Scroll down one viewport |
| `scroll_up` | - | Scroll up one viewport |
| `navigate` | `url: str` | Navigate to URL |

#### Screenshot Management

**Session ID Format**: `YYYYMMDD_HHMMSS_<uuid>`
- Example: `20250117_103045_a1b2c3d4`

**Directory Structure**:
```
output_screenshots/
└── 20250117_103045_a1b2c3d4/
    ├── step_01_initial_HHMMSS.png
    ├── step_02_click_HHMMSS.png
    ├── step_03_type_HHMMSS.png
    └── step_04_final_HHMMSS.png
```

**Naming Convention**: `step_NN_<action>_HHMMSS.png`

#### Coordinate System

Gemini uses normalized coordinates (0-999):
- Top-left: (0, 0)
- Bottom-right: (999, 999)
- Center: (500, 500)

Conversion to pixels (1280x720 viewport):
```python
pixel_x = (x / 1000) * 1280
pixel_y = (y / 1000) * 720
```

---

## Content-Gen Demo Application

### Overview

Content-Gen is a full-stack application for generating AI videos using OpenAI's Sora API. It demonstrates the collaborative capabilities of the agent system.

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Vue 3 Frontend │◄────────┤  FastAPI Backend│
│   (Port 3333)   │  HTTP   │   (Port 4444)   │
└─────────────────┘         └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ OpenAI Sora API │
                            │ Video Generation│
                            └─────────────────┘
```

---

### Backend (`apps/content-gen/backend/`)

#### Configuration (`config.py`)

```python
class Settings(BaseSettings):
    # API Keys
    openai_api_key: str

    # Server
    host: str = "0.0.0.0"
    port: int = 4444

    # Storage
    videos_dir: Path = Path("videos")

    # CORS
    cors_origins: list[str] = ["http://localhost:3333"]

    # Sora Models
    default_model: str = "sora-2"
    default_duration: int = 4
    default_resolution: str = "1280x720"
```

#### API Endpoints (`routers/videos.py`)

##### 1. Create Video
```
POST /api/v1/videos
```

**Request Body**:
```json
{
  "prompt": "A sunset over mountains",
  "model": "sora-2",
  "duration": 4,
  "resolution": "1280x720",
  "reference_image_base64": "optional-base64-string"
}
```

**Response**:
```json
{
  "id": "gen-abc123",
  "status": "pending",
  "prompt": "A sunset over mountains",
  "model": "sora-2",
  "duration": 4,
  "resolution": "1280x720",
  "created_at": "2025-01-17T10:30:00Z"
}
```

##### 2. Get Video Status
```
GET /api/v1/videos/{id}
```

**Response**:
```json
{
  "id": "gen-abc123",
  "status": "completed",
  "progress": 100,
  "video_url": "/api/v1/videos/gen-abc123/content?type=video",
  "thumbnail_url": "/api/v1/videos/gen-abc123/content?type=thumbnail"
}
```

**Status Values**: `pending`, `processing`, `completed`, `failed`

##### 3. Poll Until Complete
```
GET /api/v1/videos/{id}/poll?timeout=300
```

Long-polling endpoint that waits until video completes or timeout.

**Polling Strategy**:
- Interval: 2s → 4s → 8s → 10s (exponential backoff)
- Default timeout: 300s
- Max timeout: 600s

##### 4. Download Content
```
GET /api/v1/videos/{id}/content?type=video
GET /api/v1/videos/{id}/content?type=thumbnail
GET /api/v1/videos/{id}/content?type=spritesheet
```

Returns video file, thumbnail image, or spritesheet.

##### 5. List Videos
```
GET /api/v1/videos?skip=0&limit=20&status=completed&sort_by=created_at&sort_order=desc
```

**Query Parameters**:
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 20, max: 100)
- `status`: Filter by status
- `sort_by`: `created_at` or `prompt`
- `sort_order`: `asc` or `desc`

##### 6. Delete Video
```
DELETE /api/v1/videos/{id}
```

Removes video and associated files.

##### 7. Remix Video
```
POST /api/v1/videos/{id}/remix
```

**Request Body**:
```json
{
  "prompt": "Same but at dawn instead",
  "strength": 0.7
}
```

Creates variation of existing video.

#### Sora Service (`services/sora_service.py`)

##### Key Methods

**`create_video()`**
```python
async def create_video(
    self,
    prompt: str,
    model: str = "sora-2",
    duration: int = 4,
    resolution: str = "1280x720",
    reference_image: bytes | None = None,
) -> dict
```

**`get_video_status()`**
```python
async def get_video_status(self, generation_id: str) -> dict
```

**`download_video()`**
```python
async def download_video(
    self,
    generation_id: str,
    output_path: Path,
) -> Path
```

##### Supported Models

| Model | Quality | Speed | Cost |
|-------|---------|-------|------|
| sora-2 | Good | Fast | Lower |
| sora-2-pro | Excellent | Slower | Higher |

##### Supported Durations

- 4 seconds (default)
- 8 seconds
- 12 seconds

##### Supported Resolutions

| Resolution | Aspect Ratio | Use Case |
|------------|--------------|----------|
| 1280x720 | 16:9 | Landscape (default) |
| 720x1280 | 9:16 | Portrait/mobile |
| 1024x1024 | 1:1 | Square/social |
| 1920x1080 | 16:9 | Full HD |

---

### Frontend (`apps/content-gen/frontend/`)

#### Components

##### VideoCreator.vue
Form for creating new videos.

**Features**:
- Text input for prompt
- Model selector (sora-2, sora-2-pro)
- Duration selector (4s, 8s, 12s)
- Resolution selector
- Reference image upload
- Submit button with loading state

**Emits**: `video-created` event

##### VideoProgress.vue
Real-time progress tracking for generating videos.

**Features**:
- Progress bar (0-100%)
- Status badge (pending, processing, completed, failed)
- Auto-refresh every 2 seconds
- Completion notifications

**Props**: `videoId`

##### VideoLibrary.vue
Grid view of all videos with filtering and sorting.

**Features**:
- Grid layout with thumbnails
- Filter by status
- Sort by date/prompt
- Pagination controls
- Delete action
- Remix action

**Uses**: `useVideoLibrary` composable

##### VideoPlayer.vue
Full-featured video player.

**Features**:
- HTML5 video player
- Download button
- Remix button
- Metadata display (prompt, model, duration, resolution)

**Props**: `video` object

#### Composables

##### useVideoGeneration.ts
API client methods for video generation.

**Methods**:
```typescript
const {
  createVideo,
  getVideoStatus,
  pollVideoUntilComplete,
  downloadVideo,
  remixVideo,
  loading,
  error,
} = useVideoGeneration()
```

##### useVideoLibrary.ts
State management for video list.

**State**:
```typescript
const {
  videos,
  total,
  loading,
  error,
  filters,
  pagination,
  fetchVideos,
  deleteVideo,
} = useVideoLibrary()
```

#### Type Definitions (`types/video.ts`)

```typescript
interface Video {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  prompt: string
  model: string
  duration: number
  resolution: string
  progress: number
  video_url?: string
  thumbnail_url?: string
  created_at: string
  completed_at?: string
  error_message?: string
}

interface CreateVideoRequest {
  prompt: string
  model?: string
  duration?: number
  resolution?: string
  reference_image_base64?: string
}
```

---

## Observability & Hooks

### Hook System Architecture

Claude Code supports hooks that trigger on specific events. This project uses hooks for:
1. **Observability** - Stream events to monitoring dashboard
2. **Notifications** - User alerts with optional TTS
3. **Summarization** - AI-generated event summaries

### Hook Types

| Hook | Trigger | File |
|------|---------|------|
| PreToolUse | Before tool execution | `pre_tool_use.py` |
| PostToolUse | After tool execution | `post_tool_use.py` |
| Notification | Agent notifications | `notification.py` |
| Stop | Session end | `stop.py` |
| SubagentStop | Subagent completion | `send_event.py` |
| PreCompact | Before context compression | `send_event.py` |
| UserPromptSubmit | User input | `send_event.py` |

### Configuration (`.claude/settings.json`)

```json
{
  "hooks": {
    "UserPromptSubmit": [".claude/hooks/send_event.py"],
    "PreToolUse": [".claude/hooks/pre_tool_use.py"],
    "PostToolUse": [".claude/hooks/post_tool_use.py"],
    "Notification": [".claude/hooks/notification.py"],
    "Stop": [".claude/hooks/stop.py"],
    "SubagentStop": [".claude/hooks/send_event.py"],
    "PreCompact": [".claude/hooks/send_event.py"]
  }
}
```

### Event Streaming (`send_event.py`)

Forwards hook events to observability server at `http://localhost:4000/api/events`.

**Event Payload**:
```json
{
  "hook_type": "PostToolUse",
  "session_id": "uuid-here",
  "timestamp": "2025-01-17T10:30:00Z",
  "payload": {
    "tool_name": "Edit",
    "parameters": {...},
    "result": {...}
  },
  "summary": "AI-generated event summary",
  "chat_transcript": [...] // Only for Stop events
}
```

### AI Summarization (`utils/summarizer.py`)

Uses Claude Haiku or OpenAI to generate concise event summaries.

**Example**:
- Input: Full tool use event with parameters and results
- Output: "Modified VideoLibrary.vue to add delete button with confirmation dialog"

### Text-to-Speech Integration

Three TTS engines supported:

#### 1. OpenAI TTS (`utils/tts/openai_tts.py`)
```python
speak("Video generation complete", voice="nova")
```

#### 2. ElevenLabs (`utils/tts/elevenlabs_tts.py`)
```python
speak("Video generation complete", voice_id="...")
```

#### 3. pyttsx3 (`utils/tts/pyttsx3_tts.py`)
```python
speak("Video generation complete")  # Offline, no API key needed
```

---

## API Reference

### OpenAI Realtime Voice Agent Tools

#### `list_agents()`
Query active agents.

**Returns**:
```json
{
  "agents": [
    {
      "name": "nova",
      "type": "agentic_coding",
      "tool": "claude_code",
      "status": "active",
      "last_command": "Add delete button"
    }
  ]
}
```

#### `create_agent(tool, type, agent_name, working_directory)`
Spawn new Claude or Gemini agent.

**Parameters**:
- `tool`: "claude_code" or "gemini"
- `type`: "agentic_coding" or "browser_automation"
- `agent_name`: Unique identifier
- `working_directory`: Optional path (default: apps/content-gen)

**Returns**: Agent metadata

#### `command_agent(agent_name, prompt)`
Send task to agent.

**Parameters**:
- `agent_name`: Target agent identifier
- `prompt`: Task description

**Returns**: Task acknowledgment

#### `check_agent_result(agent_name)`
Read operator logs.

**Returns**: Operator log contents, status, blockers

#### `delete_agent(agent_name)`
Remove agent session.

**Returns**: Deletion confirmation

#### `browser_use(task_description)`
Direct browser automation (without creating persistent agent).

**Parameters**:
- `task_description`: What to do in browser

**Returns**: Results and screenshot paths

#### `read_file(file_path)`
Read file contents.

**Parameters**:
- `file_path`: Absolute or relative path

**Returns**: File contents

#### `open_file(file_path)`
Open file in VS Code or default application.

**Parameters**:
- `file_path`: Path to file

**Returns**: Confirmation

#### `report_costs()`
Get token usage and cost analysis.

**Returns**:
```json
{
  "total_tokens": 150000,
  "prompt_tokens": 100000,
  "completion_tokens": 50000,
  "estimated_cost_usd": 1.50,
  "by_model": {...}
}
```

---

## Configuration

### Environment Variables

#### Required

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Google
GEMINI_API_KEY=...
```

#### Optional

```bash
# Premium TTS
ELEVENLABS_API_KEY=...

# Future extensibility
GROQ_API_KEY=...
DEEPSEEK_API_KEY=...

# Observability
OBSERVABILITY_SERVER_URL=http://localhost:4000
```

### Command-Line Arguments

```bash
uv run big_three_realtime_agents.py [OPTIONS]
```

**Options**:
- `--mode`: text | voice-to-text | voice-to-voice (default: text)
- `--prompt`: Initial prompt for auto-mode
- `--timeout`: Auto-mode timeout in seconds
- `--system-prompt`: Custom system prompt file

**Examples**:
```bash
# Text mode
uv run big_three_realtime_agents.py --mode text

# Voice mode
uv run big_three_realtime_agents.py --mode voice-to-voice

# Auto mode with timeout
uv run big_three_realtime_agents.py --prompt "Create a video of mountains" --timeout 300
```

---

## Development Workflows

### Workflow 1: Voice-Driven Frontend Development

```
1. User: "Create a Claude agent called nova"
   ↓
2. Voice Agent: create_agent(tool="claude_code", agent_name="nova")
   ↓
3. User: "Have nova add a delete button to the video library"
   ↓
4. Voice Agent: command_agent(agent_name="nova", prompt="...")
   ↓
5. Claude Agent:
   - Reads VideoLibrary.vue
   - Plans implementation
   - Adds delete button with confirmation dialog
   - Uses browser_use tool to validate UI
   ↓
6. Gemini Browser Agent:
   - Opens http://localhost:3333
   - Takes screenshots
   - Validates button appearance and functionality
   ↓
7. Claude Agent:
   - Updates operator log with results
   - Returns completion status
   ↓
8. Voice Agent: "Done! The delete button is live."
```

### Workflow 2: Automated Video Generation

```bash
uv run big_three_realtime_agents.py \
  --prompt "Create a sora-2 video of a sunset over mountains, 8 seconds long"
```

```
1. Voice agent receives prompt
   ↓
2. Creates Claude agent
   ↓
3. Claude agent:
   - Calls backend POST /api/v1/videos
   - Polls GET /api/v1/videos/{id}/poll
   - Downloads completed video
   ↓
4. Voice agent reports video location
```

### Workflow 3: Full-Stack Feature Development

```
1. User: "/quick-plan Add video remix feature to UI"
   ↓
2. Slash command expands to planning prompt
   ↓
3. Claude creates implementation plan in specs/
   ↓
4. User: "/build specs/remix-feature.md"
   ↓
5. Claude agent:
   - Backend: Adds remix endpoint
   - Frontend: Adds remix button to VideoPlayer
   - Frontend: Implements remix dialog
   - Tests with browser automation
   ↓
6. User: Commits changes
```

---

## Design Patterns

### 1. Monolithic Main File

**Pattern**: Single 3228-line file contains all three agent classes

**Rationale**:
- Self-contained deployment
- Single entry point: `uv run big_three_realtime_agents.py`
- No complex import structure

**Trade-offs**:
- Harder to maintain and navigate
- Tight coupling between components
- Noted in README as area for improvement

### 2. Operator Log Pattern

**Pattern**: Each coding task gets a unique markdown file

**Structure**:
```markdown
# Task: [AI-generated descriptive name]

## Plan
...

## Progress
...

## Results
...
```

**Benefits**:
- Human-readable audit trail
- Resumable context for agents
- Git-friendly (diff-able)
- LLM-parseable for analysis

### 3. Registry-Based Session Management

**Pattern**: JSON files track active agent sessions

**Location**: `agents/<tool_slug>/registry.json`

**Benefits**:
- Simple, no database dependency
- Version-controlled
- Easy to inspect and debug

**Concurrency**: Thread locks prevent race conditions

### 4. Tool Injection Pattern

**Pattern**: Claude agents get a `browser_use` tool dynamically injected

**Implementation**:
```python
browser_tool = self._create_browser_tool(agent_name, screenshot_dir)
tools.append(browser_tool)
```

**Purpose**: Enable Claude to validate its own frontend work using Gemini

### 5. Dual-Mode Audio Control

**Pattern**: Both manual and automatic microphone pause

**Manual**: Shift+Space toggle
**Auto**: During agent speech (prevents feedback loop)

**Audio Feedback**:
- 520Hz beep: Microphone resumed
- 380Hz beep: Microphone paused

### 6. Event-Driven Observability

**Pattern**: Hooks trigger on tool use, notifications, session events

**Flow**:
```
Event → Hook → AI Summarization → HTTP POST → Observability Dashboard
```

**Benefits**:
- Real-time monitoring
- AI-powered event understanding
- Minimal performance impact

### 7. Composable Vue Architecture

**Pattern**: Logic extracted to `use*` composables

**Example**:
```typescript
// VideoLibrary.vue
const { videos, fetchVideos, deleteVideo } = useVideoLibrary()

// useVideoLibrary.ts
export function useVideoLibrary() {
  const videos = ref<Video[]>([])
  const fetchVideos = async () => { ... }
  const deleteVideo = async (id: string) => { ... }
  return { videos, fetchVideos, deleteVideo }
}
```

**Benefits**:
- Testable business logic
- Reusable across components
- Separation of concerns

### 8. Exponential Backoff Polling

**Pattern**: Start fast, increase to maximum

**Polling Intervals**: 2s → 4s → 8s → 10s

**Purpose**:
- Responsive early (when completion likely)
- Efficient later (when still processing)

**Timeout**: 300s default, 600s max

### 9. Zero-Install Hooks

**Pattern**: Inline PEP 723 script metadata

```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["anthropic", "openai"]
# ///
```

**Benefits**:
- No separate venv needed
- Self-contained scripts
- Automatic dependency installation

---

## Data Flow

### Voice Command to Code Change

```
User Voice Input
    ↓
OpenAI Realtime API (WebSocket)
    ↓
Voice Agent (audio → text transcription)
    ↓
Function Call: command_agent(agent_name="nova", prompt="Add feature X")
    ↓
ClaudeCodeAgenticCoder
    ↓
Claude Agent SDK (API call)
    ↓
Claude reads files (Read tool)
    ↓
Claude plans implementation
    ↓
Claude makes changes (Edit/Write tools)
    ↓
Claude validates with browser_use tool
    ↓
GeminiBrowserAgent
    ↓
Playwright opens browser
    ↓
Screenshots → Gemini Computer Use API
    ↓
Gemini returns actions (click, type, etc.)
    ↓
Browser executes actions
    ↓
Validation results → Claude
    ↓
Claude updates operator log
    ↓
Operator log → Voice Agent
    ↓
Voice Agent → OpenAI TTS
    ↓
User hears: "Feature X has been added and validated"
```

### Video Generation Flow

```
User Request: "Create a video of mountains"
    ↓
Voice Agent: command_agent(agent_name="auto", prompt="...")
    ↓
Claude Agent
    ↓
HTTP POST /api/v1/videos
    ↓
FastAPI Backend
    ↓
SoraService.create_video()
    ↓
OpenAI Sora API (async)
    ↓
Sora generates video
    ↓
Backend polls SoraService.get_video_status()
    ↓
Status: completed
    ↓
SoraService.download_video()
    ↓
Video saved to videos/ directory
    ↓
Response with video_url
    ↓
Claude Agent logs video path
    ↓
Voice Agent: "Your mountain video is ready at videos/gen-abc123.mp4"
```

---

## Summary

This codebase represents a sophisticated **multi-agent orchestration system** that demonstrates:

1. **Voice-first interaction** with AI agents
2. **Specialized agent delegation** (coding vs. browser automation)
3. **Real-world demo application** (Sora video generation)
4. **Production-ready patterns** (observability, session management, error handling)
5. **Practical deployment** (zero-install hooks, uv package manager)

The architecture emphasizes **pragmatic simplicity** (JSON registries, markdown logs) while maintaining **enterprise-grade observability** (event streaming, AI summarization, TTS notifications).

Key strengths:
- Unified voice interface to multiple AI capabilities
- Session persistence and resumability
- Built-in validation (browser agents validate code agents' work)
- Comprehensive audit trail (operator logs + observability events)
- Self-contained deployment (uv run with inline dependencies)

This system serves as both a **working application** and a **reference architecture** for building voice-controlled multi-agent systems.
