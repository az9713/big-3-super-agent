# Feature 10: Session Persistence & Recovery System

## Overview

The **Session Persistence & Recovery System** provides comprehensive session management capabilities for the Big Three Realtime Agents, enabling conversation history persistence, session resume, crash recovery, and state management across sessions.

**Version:** 1.0.0
**Status:** ✅ Implemented
**Implementation:** `apps/realtime-poc/features/session_persistence.py`

## Problem Statement

Without session persistence, the system faces several limitations:
- **No conversation history**: Previous interactions are lost when sessions end
- **Cannot resume work**: Interrupted sessions cannot be continued
- **No crash recovery**: System failures result in complete loss of context
- **No audit trail**: Historical conversations are not accessible
- **Poor long-term learning**: Agents cannot learn from past interactions

## Solution

The Session Persistence & Recovery System provides:
- **Automatic persistence**: Conversation history saved in real-time
- **Session resume**: Continue interrupted work seamlessly
- **Crash recovery**: Automatic detection and recovery from crashes
- **Snapshots & checkpoints**: Point-in-time session state capture
- **Session rollback**: Restore to previous states
- **Export/import**: Share and archive sessions
- **Search & filter**: Find past conversations

## Architecture

### Components

```
SessionManager (High-level API)
├── SessionStore (SQLite persistence)
│   ├── sessions table
│   ├── messages table
│   └── snapshots table
├── RecoveryManager (Crash recovery)
│   ├── Crash detection
│   ├── Recovery points
│   └── Rollback
└── SessionExporter (Import/export)
    ├── JSON export
    ├── Compressed export
    └── Session import
```

### Database Schema

**sessions table:**
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,  -- active, paused, completed, crashed, recovered
    title TEXT,
    description TEXT,
    message_count INTEGER DEFAULT 0,
    agent_count INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,
    metadata TEXT
)
```

**messages table:**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- user, assistant, system, tool
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
)
```

**snapshots table:**
```sql
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    snapshot_type TEXT NOT NULL,  -- manual, auto, crash, checkpoint
    timestamp TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    agent_states TEXT NOT NULL,
    system_state TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
)
```

### Data Models

**Session:**
```python
@dataclass
class Session:
    id: str
    started_at: str
    ended_at: Optional[str]
    status: SessionStatus  # ACTIVE, PAUSED, COMPLETED, CRASHED, RECOVERED
    title: Optional[str]
    description: Optional[str]
    message_count: int = 0
    agent_count: int = 0
    total_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Message:**
```python
@dataclass
class Message:
    id: str
    session_id: str
    role: MessageRole  # USER, ASSISTANT, SYSTEM, TOOL
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**SessionSnapshot:**
```python
@dataclass
class SessionSnapshot:
    id: str
    session_id: str
    snapshot_type: SnapshotType  # MANUAL, AUTO, CRASH, CHECKPOINT
    timestamp: str
    message_count: int
    agent_states: List[AgentState]
    system_state: Dict[str, Any]
    description: Optional[str] = None
```

**AgentState:**
```python
@dataclass
class AgentState:
    agent_name: str
    agent_type: str  # claude_code, gemini, etc.
    session_id: str
    status: str
    current_task: Optional[str]
    operator_file: Optional[str]
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Usage

### Basic Session Management

**Start a new session:**
```python
from features.session_persistence import SessionManager

# Initialize manager
manager = SessionManager()

# Start session
session = manager.start_session(
    title="Video Generation Feature Development",
    description="Implementing video generation UI improvements"
)

print(f"Session started: {session.id}")
```

**Add messages to session:**
```python
from features.session_persistence import MessageRole

# Add user message
manager.add_message(
    role=MessageRole.USER,
    content="Create a new video component",
    metadata={"source": "voice"}
)

# Add assistant message
manager.add_message(
    role=MessageRole.ASSISTANT,
    content="I'll create the video component now...",
    metadata={"agent": "claude_code"}
)
```

**End a session:**
```python
# End current session
manager.end_session()

# Or end specific session
manager.end_session(session_id="session-123")
```

### Session Resume

**Resume an interrupted session:**
```python
# List available sessions
sessions = manager.list_sessions(status=SessionStatus.ACTIVE)

for session in sessions:
    print(f"{session.id}: {session.title} ({session.message_count} messages)")

# Resume specific session
recovery_data = manager.resume_session("session-123")

print(f"Session resumed: {recovery_data['session'].title}")
print(f"Messages loaded: {len(recovery_data['messages'])}")
print(f"Agent states: {len(recovery_data['agent_states'])}")

# Get conversation history
history = recovery_data['messages']
for msg in history:
    print(f"[{msg.role.value}] {msg.content[:50]}...")
```

### Crash Recovery

**Detect crashed sessions:**
```python
from features.session_persistence import RecoveryManager

recovery = RecoveryManager(manager.store)

# Detect crashed sessions (active for >24h with no activity for >2h)
crashed = recovery.detect_crashed_sessions()

for session in crashed:
    print(f"Crashed session detected: {session.id}")
    print(f"Started: {session.started_at}")
```

**Recover from crash:**
```python
# Recover crashed session
recovery_data = recovery.recover_session("crashed-session-id")

session = recovery_data['session']
messages = recovery_data['messages']
agent_states = recovery_data['agent_states']
system_state = recovery_data['system_state']

print(f"Recovered session: {session.title}")
print(f"Status: {session.status.value}")  # RECOVERED
print(f"Messages: {len(messages)}")

# Restore agent states
for agent_state in agent_states:
    print(f"Agent {agent_state.agent_name}: {agent_state.status}")
    # Re-create or reconnect to agent
```

### Snapshots & Checkpoints

**Create automatic snapshots:**
```python
# Auto-snapshot every 100 messages (default)
manager.auto_snapshot_interval = 100

# Add messages (auto-snapshot triggers automatically)
for i in range(150):
    manager.add_message(
        role=MessageRole.USER,
        content=f"Message {i}"
    )

# Snapshot created at message 100
```

**Create manual checkpoint:**
```python
from features.session_persistence import AgentState

# Get current agent states
agent_states = [
    AgentState(
        agent_name="nova",
        agent_type="claude_code",
        session_id=session.id,
        status="active",
        current_task="Implementing video component",
        operator_file="operator_123.txt",
        created_at=datetime.now().isoformat(),
        metadata={"task_progress": 0.75}
    )
]

# Create checkpoint
checkpoint = manager.create_checkpoint(
    description="Video component UI complete, starting backend",
    agent_states=agent_states,
    system_state={"phase": "backend", "tests_passing": True}
)

print(f"Checkpoint created: {checkpoint.id}")
print(f"Description: {checkpoint.description}")
```

**List snapshots:**
```python
snapshots = manager.store.get_snapshots(session.id)

for snap in snapshots:
    print(f"Snapshot: {snap.snapshot_type.value}")
    print(f"Time: {snap.timestamp}")
    print(f"Messages: {snap.message_count}")
    print(f"Description: {snap.description}")
```

### Rollback

**Rollback to previous checkpoint:**
```python
# Get snapshot ID
snapshots = manager.store.get_snapshots(session.id)
checkpoint = snapshots[0]  # Latest snapshot

# Rollback
rollback_data = recovery.rollback_to_snapshot(
    session.id,
    checkpoint.id
)

# Restore state
session = rollback_data['session']
messages = rollback_data['messages']  # Only messages up to checkpoint
agent_states = rollback_data['agent_states']
system_state = rollback_data['system_state']

print(f"Rolled back to: {checkpoint.description}")
print(f"Messages after rollback: {len(messages)}")
```

### Export & Import

**Export session:**
```python
from features.session_persistence import SessionExporter

exporter = SessionExporter(manager.store)

# Export as JSON
json_path = exporter.export_session(
    session.id,
    format="json",
    include_snapshots=True
)

print(f"Session exported to: {json_path}")

# Export as compressed JSON
gz_path = exporter.export_session(
    session.id,
    format="json.gz",
    include_snapshots=True
)

print(f"Compressed export: {gz_path}")
```

**Import session:**
```python
# Import from file
imported_session = exporter.import_session(json_path)

print(f"Session imported: {imported_session.id}")
print(f"Title: {imported_session.title}")
print(f"Messages: {imported_session.message_count}")

# Session gets new ID on import
# Original: session-123
# Imported: session-456
```

### Search & Filter

**List sessions with filters:**
```python
# Get all active sessions
active = manager.list_sessions(status=SessionStatus.ACTIVE)

# Get all completed sessions
completed = manager.list_sessions(status=SessionStatus.COMPLETED)

# Get all sessions (with pagination)
all_sessions = manager.list_sessions(limit=50)

# Sort by date
for session in all_sessions:
    print(f"{session.started_at}: {session.title}")
```

**Get session history:**
```python
# Get full conversation history
history = manager.get_session_history(session.id)

# Get paginated history
recent = manager.get_session_history(session.id, limit=50)

# Process messages
for msg in history:
    if msg.role == MessageRole.USER:
        print(f"User: {msg.content}")
    elif msg.role == MessageRole.ASSISTANT:
        print(f"Assistant: {msg.content}")
```

## Integration with Voice Agent

### Integration Points

**1. Session Start (voice agent initialization):**
```python
# In OpenAIRealtimeVoiceAgent.__init__
from features.session_persistence import SessionManager, MessageRole

self.session_manager = SessionManager()
self.current_session = self.session_manager.start_session(
    title="Voice Agent Session",
    description=f"Started at {datetime.now().isoformat()}"
)
```

**2. Message Tracking (every user/assistant interaction):**
```python
# When user sends message
def on_user_message(self, message: str):
    self.session_manager.add_message(
        role=MessageRole.USER,
        content=message,
        metadata={"source": "voice", "timestamp": time.time()}
    )

# When assistant responds
def on_assistant_message(self, message: str):
    self.session_manager.add_message(
        role=MessageRole.ASSISTANT,
        content=message,
        metadata={"model": "gpt-4o-realtime", "timestamp": time.time()}
    )
```

**3. Periodic Snapshots (every N messages or time interval):**
```python
# Create snapshot with current state
def create_snapshot(self):
    agent_states = []

    # Capture all active agent states
    for agent_name, agent in self.agents.items():
        agent_state = AgentState(
            agent_name=agent_name,
            agent_type=agent.agent_type,
            session_id=self.current_session.id,
            status=agent.status,
            current_task=agent.current_task,
            operator_file=agent.operator_file,
            created_at=agent.created_at,
            metadata=agent.get_state_metadata()
        )
        agent_states.append(agent_state)

    # Create snapshot
    self.session_manager.create_auto_snapshot(
        self.current_session.id,
        agent_states,
        {
            "total_cost": self.get_total_cost(),
            "active_agents": len(self.agents),
            "system_status": "healthy"
        }
    )
```

**4. Session End (graceful shutdown):**
```python
def shutdown(self):
    # Create final snapshot
    self.create_snapshot()

    # End session
    self.session_manager.end_session()
```

**5. Crash Recovery (on startup):**
```python
def on_startup(self):
    # Check for crashed sessions
    crashed = self.session_manager.recovery.detect_crashed_sessions()

    if crashed:
        print(f"Found {len(crashed)} crashed sessions")

        # Ask user if they want to recover
        for session in crashed:
            print(f"Session: {session.title}")
            print(f"Messages: {session.message_count}")

            # Auto-recover or prompt user
            recovery_data = self.session_manager.resume_session(session.id)

            # Restore state
            self._restore_session_state(recovery_data)
```

### Voice Commands

Add these voice commands to interact with session persistence:

```python
# In voice agent tools
def save_checkpoint(self, description: str) -> dict:
    """Create a manual checkpoint with description"""
    agent_states = self._get_current_agent_states()
    system_state = self._get_current_system_state()

    checkpoint = self.session_manager.create_checkpoint(
        description=description,
        agent_states=agent_states,
        system_state=system_state
    )

    return {
        "success": True,
        "checkpoint_id": checkpoint.id,
        "message": f"Checkpoint saved: {description}"
    }

def list_checkpoints(self) -> dict:
    """List all checkpoints for current session"""
    snapshots = self.session_manager.store.get_snapshots(
        self.current_session.id
    )

    checkpoints = [s for s in snapshots if s.snapshot_type == SnapshotType.CHECKPOINT]

    return {
        "checkpoints": [
            {
                "id": c.id,
                "description": c.description,
                "timestamp": c.timestamp,
                "message_count": c.message_count
            }
            for c in checkpoints
        ]
    }

def rollback_to_checkpoint(self, checkpoint_id: str) -> dict:
    """Rollback to a previous checkpoint"""
    rollback_data = self.session_manager.recovery.rollback_to_snapshot(
        self.current_session.id,
        checkpoint_id
    )

    # Restore state
    self._restore_session_state(rollback_data)

    return {
        "success": True,
        "message": f"Rolled back to checkpoint",
        "messages_restored": len(rollback_data['messages'])
    }

def export_session(self) -> dict:
    """Export current session"""
    path = self.session_manager.export_current_session(format="json")

    return {
        "success": True,
        "path": str(path),
        "message": f"Session exported to {path}"
    }
```

**Example voice interactions:**
```
User: "Save a checkpoint with description 'video UI complete'"
Assistant: "Checkpoint saved: video UI complete"

User: "List my checkpoints"
Assistant: "You have 3 checkpoints:
1. Initial setup (10 messages)
2. Backend implementation (45 messages)
3. Video UI complete (78 messages)"

User: "Roll back to checkpoint 2"
Assistant: "Rolled back to 'Backend implementation'. Session now has 45 messages."

User: "Export this session"
Assistant: "Session exported to sessions/exports/session_abc123_20250118.json"
```

## Performance Considerations

### Database Performance

- **Indexes**: Created on frequently queried columns (session_id, timestamp, status)
- **Connection pooling**: Single connection per thread with lock
- **Batch operations**: Messages added individually but with minimal overhead
- **Query optimization**: Efficient queries with proper indexing

### Memory Management

- **Lazy loading**: Messages loaded on demand, not all at once
- **Pagination**: Support for loading messages in chunks
- **Snapshot compression**: Large system states can be compressed
- **Cleanup**: Old sessions can be archived and removed

### Auto-Snapshot Strategy

**Default strategy:**
- Auto-snapshot every 100 messages
- Adjustable via `manager.auto_snapshot_interval`

**Alternative strategies:**
```python
# Time-based snapshots
import threading

def auto_snapshot_timer():
    while True:
        time.sleep(300)  # Every 5 minutes
        if manager.current_session:
            manager.create_auto_snapshot(
                manager.current_session.id,
                agent_states,
                system_state
            )

# Start timer
threading.Thread(target=auto_snapshot_timer, daemon=True).start()
```

```python
# Event-based snapshots
def on_critical_event(event_type: str):
    # Snapshot before critical operations
    if event_type in ["agent_created", "large_code_change", "git_commit"]:
        manager.create_auto_snapshot(
            manager.current_session.id,
            agent_states,
            system_state
        )
```

## Error Handling

### Crash Detection Logic

```python
def detect_crashed_sessions(self) -> List[Session]:
    sessions = self.store.list_sessions(status=SessionStatus.ACTIVE)
    crashed = []
    now = datetime.now()

    for session in sessions:
        started_at = datetime.fromisoformat(session.started_at)
        age = now - started_at

        # Session active for >24 hours
        if age > timedelta(hours=24):
            messages = self.store.get_messages(session.id, limit=1)

            if messages:
                last_message = datetime.fromisoformat(messages[-1].timestamp)
                inactive_time = now - last_message

                # No activity for >2 hours = crashed
                if inactive_time > timedelta(hours=2):
                    session.status = SessionStatus.CRASHED
                    self.store.update_session(session)
                    crashed.append(session)

    return crashed
```

### Recovery Strategy

**On startup:**
1. Detect crashed sessions
2. Present list to user
3. Offer auto-recovery or manual selection
4. Restore session state from latest snapshot
5. Mark session as RECOVERED

**Manual recovery:**
```python
# User explicitly recovers session
recovery_data = manager.resume_session("session-id")

# Restore conversation context
for msg in recovery_data['messages_after_snapshot']:
    display_message(msg)

# Restore agent states
for agent_state in recovery_data['agent_states']:
    recreate_agent(agent_state)

# Continue from last point
```

## Testing

### Unit Tests

```python
import pytest
from features.session_persistence import (
    SessionManager,
    MessageRole,
    SessionStatus
)

def test_session_creation():
    manager = SessionManager(db_path=Path("test.db"))

    session = manager.start_session(title="Test Session")

    assert session.id is not None
    assert session.title == "Test Session"
    assert session.status == SessionStatus.ACTIVE

def test_message_persistence():
    manager = SessionManager(db_path=Path("test.db"))
    session = manager.start_session()

    manager.add_message(MessageRole.USER, "Hello")
    manager.add_message(MessageRole.ASSISTANT, "Hi there")

    history = manager.get_session_history(session.id)

    assert len(history) == 2
    assert history[0].role == MessageRole.USER
    assert history[0].content == "Hello"

def test_session_resume():
    manager = SessionManager(db_path=Path("test.db"))

    # Create and populate session
    session = manager.start_session(title="Resume Test")
    manager.add_message(MessageRole.USER, "Test message")

    # End session
    manager.end_session()

    # Resume session
    recovery_data = manager.resume_session(session.id)

    assert recovery_data['session'].title == "Resume Test"
    assert len(recovery_data['messages']) == 1

def test_checkpoint_rollback():
    manager = SessionManager(db_path=Path("test.db"))
    session = manager.start_session()

    # Add messages
    manager.add_message(MessageRole.USER, "Message 1")

    # Create checkpoint
    checkpoint = manager.create_checkpoint(
        description="After message 1",
        agent_states=[],
        system_state={}
    )

    # Add more messages
    manager.add_message(MessageRole.USER, "Message 2")
    manager.add_message(MessageRole.USER, "Message 3")

    # Rollback
    rollback_data = manager.recovery.rollback_to_snapshot(
        session.id,
        checkpoint.id
    )

    # Should only have 1 message
    assert len(rollback_data['messages']) == 1
```

### Integration Tests

```python
def test_crash_recovery():
    manager = SessionManager(db_path=Path("test.db"))

    # Simulate crashed session
    session = manager.start_session()
    manager.add_message(MessageRole.USER, "Before crash")

    # Create snapshot
    manager.create_auto_snapshot(session.id, [], {})

    # Simulate crash (leave session active)
    # ... time passes ...

    # Detect crash
    crashed = manager.recovery.detect_crashed_sessions()

    assert len(crashed) > 0

    # Recover
    recovery_data = manager.resume_session(crashed[0].id)

    assert recovery_data['session'].status == SessionStatus.RECOVERED
```

## Future Enhancements

1. **Cloud Sync**: Sync sessions across devices
2. **Session Sharing**: Share sessions with team members
3. **Advanced Search**: Full-text search across all sessions
4. **Session Analytics**: Analyze conversation patterns
5. **Auto-Cleanup**: Automatic archival of old sessions
6. **Session Merge**: Combine multiple sessions
7. **Differential Snapshots**: Only store changes between snapshots
8. **Encryption**: Encrypt sensitive session data

## API Reference

See `apps/realtime-poc/features/session_persistence.py` for complete API documentation.

### Key Classes

- `SessionManager`: High-level session management
- `SessionStore`: SQLite persistence layer
- `RecoveryManager`: Crash recovery and rollback
- `SessionExporter`: Import/export functionality
- `Session`: Session metadata
- `Message`: Conversation message
- `SessionSnapshot`: Point-in-time snapshot
- `AgentState`: Agent state capture

### Key Methods

- `start_session()`: Begin new session
- `end_session()`: Complete session
- `add_message()`: Add message to session
- `resume_session()`: Resume interrupted session
- `create_checkpoint()`: Manual snapshot
- `rollback_to_snapshot()`: Restore previous state
- `export_session()`: Export to file
- `import_session()`: Import from file
- `detect_crashed_sessions()`: Find crashed sessions

## Conclusion

The Session Persistence & Recovery System provides robust session management for the Big Three Realtime Agents, enabling continuous operation, crash recovery, and long-term conversation history. This foundation supports future features like multi-device sync, team collaboration, and advanced analytics.
