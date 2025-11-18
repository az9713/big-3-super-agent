"""
Session Persistence & Recovery System for Big Three Realtime Agents

This module provides comprehensive session management capabilities including:
- Automatic conversation history persistence
- Session resume and recovery from interruptions
- Crash recovery with automatic restore
- Manual snapshots and checkpoints
- Session rollback to previous states
- Session export/import
- Session search and filtering

Author: Big Three Realtime Agents
Version: 1.0.0
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum
import threading
import shutil
import gzip
import pickle


class SessionStatus(Enum):
    """Session status values"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CRASHED = "crashed"
    RECOVERED = "recovered"


class MessageRole(Enum):
    """Message role values"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class SnapshotType(Enum):
    """Snapshot type values"""
    MANUAL = "manual"
    AUTO = "auto"
    CRASH = "crash"
    CHECKPOINT = "checkpoint"


@dataclass
class Message:
    """Represents a single message in the conversation"""
    id: str
    session_id: str
    role: MessageRole
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['role'] = self.role.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create from dictionary"""
        data = data.copy()
        data['role'] = MessageRole(data['role'])
        return cls(**data)


@dataclass
class AgentState:
    """Represents the state of an agent at a point in time"""
    agent_name: str
    agent_type: str  # claude_code, gemini, etc.
    session_id: str
    status: str
    current_task: Optional[str]
    operator_file: Optional[str]
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentState':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class SessionSnapshot:
    """Represents a point-in-time snapshot of a session"""
    id: str
    session_id: str
    snapshot_type: SnapshotType
    timestamp: str
    message_count: int
    agent_states: List[AgentState]
    system_state: Dict[str, Any]
    description: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['snapshot_type'] = self.snapshot_type.value
        data['agent_states'] = [s.to_dict() for s in self.agent_states]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'SessionSnapshot':
        """Create from dictionary"""
        data = data.copy()
        data['snapshot_type'] = SnapshotType(data['snapshot_type'])
        data['agent_states'] = [AgentState.from_dict(s) for s in data['agent_states']]
        return cls(**data)


@dataclass
class Session:
    """Represents a voice agent session"""
    id: str
    started_at: str
    ended_at: Optional[str]
    status: SessionStatus
    title: Optional[str]
    description: Optional[str]
    message_count: int = 0
    agent_count: int = 0
    total_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        """Create from dictionary"""
        data = data.copy()
        data['status'] = SessionStatus(data['status'])
        return cls(**data)


class SessionStore:
    """
    Persistent storage for session data using SQLite.

    Stores:
    - Session metadata
    - Conversation messages
    - Snapshots
    - Agent states
    """

    def __init__(self, db_path: Path = None):
        """Initialize session store"""
        if db_path is None:
            db_path = Path("sessions/session_store.db")

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    message_count INTEGER DEFAULT 0,
                    agent_count INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    metadata TEXT
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    snapshot_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message_count INTEGER NOT NULL,
                    agent_states TEXT NOT NULL,
                    system_state TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_session
                ON snapshots(session_id, timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status
                ON sessions(status, started_at)
            """)

            conn.commit()
            conn.close()

    def create_session(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Session:
        """Create a new session"""
        session = Session(
            id=str(uuid.uuid4()),
            started_at=datetime.now().isoformat(),
            ended_at=None,
            status=SessionStatus.ACTIVE,
            title=title,
            description=description,
            metadata=metadata or {}
        )

        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sessions
                (id, started_at, ended_at, status, title, description,
                 message_count, agent_count, total_cost, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.started_at,
                session.ended_at,
                session.status.value,
                session.title,
                session.description,
                session.message_count,
                session.agent_count,
                session.total_cost,
                json.dumps(session.metadata)
            ))

            conn.commit()
            conn.close()

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, started_at, ended_at, status, title, description,
                       message_count, agent_count, total_cost, metadata
                FROM sessions WHERE id = ?
            """, (session_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return Session(
                id=row[0],
                started_at=row[1],
                ended_at=row[2],
                status=SessionStatus(row[3]),
                title=row[4],
                description=row[5],
                message_count=row[6],
                agent_count=row[7],
                total_cost=row[8],
                metadata=json.loads(row[9]) if row[9] else {}
            )

    def update_session(self, session: Session):
        """Update session"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE sessions SET
                    ended_at = ?,
                    status = ?,
                    title = ?,
                    description = ?,
                    message_count = ?,
                    agent_count = ?,
                    total_cost = ?,
                    metadata = ?
                WHERE id = ?
            """, (
                session.ended_at,
                session.status.value,
                session.title,
                session.description,
                session.message_count,
                session.agent_count,
                session.total_cost,
                json.dumps(session.metadata),
                session.id
            ))

            conn.commit()
            conn.close()

    def add_message(self, message: Message):
        """Add a message to the session"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (id, session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.id,
                message.session_id,
                message.role.value,
                message.content,
                message.timestamp,
                json.dumps(message.metadata)
            ))

            # Update session message count
            cursor.execute("""
                UPDATE sessions
                SET message_count = message_count + 1
                WHERE id = ?
            """, (message.session_id,))

            conn.commit()
            conn.close()

    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a session"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            query = """
                SELECT id, session_id, role, content, timestamp, metadata
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """

            params = [session_id]

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            messages = []
            for row in rows:
                messages.append(Message(
                    id=row[0],
                    session_id=row[1],
                    role=MessageRole(row[2]),
                    content=row[3],
                    timestamp=row[4],
                    metadata=json.loads(row[5]) if row[5] else {}
                ))

            return messages

    def create_snapshot(self, snapshot: SessionSnapshot):
        """Create a snapshot"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO snapshots
                (id, session_id, snapshot_type, timestamp, message_count,
                 agent_states, system_state, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.id,
                snapshot.session_id,
                snapshot.snapshot_type.value,
                snapshot.timestamp,
                snapshot.message_count,
                json.dumps([s.to_dict() for s in snapshot.agent_states]),
                json.dumps(snapshot.system_state),
                snapshot.description
            ))

            conn.commit()
            conn.close()

    def get_snapshots(self, session_id: str) -> List[SessionSnapshot]:
        """Get snapshots for a session"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, session_id, snapshot_type, timestamp, message_count,
                       agent_states, system_state, description
                FROM snapshots
                WHERE session_id = ?
                ORDER BY timestamp DESC
            """, (session_id,))

            rows = cursor.fetchall()
            conn.close()

            snapshots = []
            for row in rows:
                snapshots.append(SessionSnapshot(
                    id=row[0],
                    session_id=row[1],
                    snapshot_type=SnapshotType(row[2]),
                    timestamp=row[3],
                    message_count=row[4],
                    agent_states=[AgentState.from_dict(s) for s in json.loads(row[5])],
                    system_state=json.loads(row[6]),
                    description=row[7]
                ))

            return snapshots

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Session]:
        """List sessions with optional filtering"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            query = """
                SELECT id, started_at, ended_at, status, title, description,
                       message_count, agent_count, total_cost, metadata
                FROM sessions
            """

            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status.value)

            query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            sessions = []
            for row in rows:
                sessions.append(Session(
                    id=row[0],
                    started_at=row[1],
                    ended_at=row[2],
                    status=SessionStatus(row[3]),
                    title=row[4],
                    description=row[5],
                    message_count=row[6],
                    agent_count=row[7],
                    total_cost=row[8],
                    metadata=json.loads(row[9]) if row[9] else {}
                ))

            return sessions


class RecoveryManager:
    """
    Manages session recovery and crash detection.

    Features:
    - Automatic crash detection
    - Session recovery
    - State restoration
    - Rollback to snapshots
    """

    def __init__(self, session_store: SessionStore):
        """Initialize recovery manager"""
        self.store = session_store
        self.recovery_dir = Path("sessions/recovery")
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

    def detect_crashed_sessions(self) -> List[Session]:
        """Detect sessions that may have crashed"""
        sessions = self.store.list_sessions(status=SessionStatus.ACTIVE)

        crashed = []
        now = datetime.now()

        for session in sessions:
            started_at = datetime.fromisoformat(session.started_at)
            age = now - started_at

            # If session is active for more than 24 hours, consider it crashed
            if age > timedelta(hours=24):
                # Check if there's recent activity
                messages = self.store.get_messages(session.id, limit=1)

                if messages:
                    last_message = datetime.fromisoformat(messages[-1].timestamp)
                    inactive_time = now - last_message

                    # No activity for 2 hours = crashed
                    if inactive_time > timedelta(hours=2):
                        session.status = SessionStatus.CRASHED
                        self.store.update_session(session)
                        crashed.append(session)

        return crashed

    def create_recovery_point(
        self,
        session_id: str,
        agent_states: List[AgentState],
        system_state: Dict[str, Any]
    ) -> SessionSnapshot:
        """Create a recovery point (automatic snapshot)"""
        session = self.store.get_session(session_id)

        snapshot = SessionSnapshot(
            id=str(uuid.uuid4()),
            session_id=session_id,
            snapshot_type=SnapshotType.AUTO,
            timestamp=datetime.now().isoformat(),
            message_count=session.message_count,
            agent_states=agent_states,
            system_state=system_state
        )

        self.store.create_snapshot(snapshot)
        return snapshot

    def create_checkpoint(
        self,
        session_id: str,
        agent_states: List[AgentState],
        system_state: Dict[str, Any],
        description: str
    ) -> SessionSnapshot:
        """Create a manual checkpoint"""
        session = self.store.get_session(session_id)

        snapshot = SessionSnapshot(
            id=str(uuid.uuid4()),
            session_id=session_id,
            snapshot_type=SnapshotType.CHECKPOINT,
            timestamp=datetime.now().isoformat(),
            message_count=session.message_count,
            agent_states=agent_states,
            system_state=system_state,
            description=description
        )

        self.store.create_snapshot(snapshot)
        return snapshot

    def recover_session(self, session_id: str) -> Dict[str, Any]:
        """Recover a crashed or interrupted session"""
        session = self.store.get_session(session_id)

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get latest snapshot
        snapshots = self.store.get_snapshots(session_id)

        if not snapshots:
            # No snapshots, recover from messages only
            messages = self.store.get_messages(session_id)
            return {
                "session": session,
                "messages": messages,
                "agent_states": [],
                "system_state": {}
            }

        latest_snapshot = snapshots[0]

        # Get messages after snapshot
        messages = self.store.get_messages(session_id)
        snapshot_time = datetime.fromisoformat(latest_snapshot.timestamp)

        messages_after_snapshot = [
            m for m in messages
            if datetime.fromisoformat(m.timestamp) > snapshot_time
        ]

        # Update session status
        session.status = SessionStatus.RECOVERED
        self.store.update_session(session)

        return {
            "session": session,
            "messages": messages,
            "messages_after_snapshot": messages_after_snapshot,
            "agent_states": latest_snapshot.agent_states,
            "system_state": latest_snapshot.system_state,
            "snapshot": latest_snapshot
        }

    def rollback_to_snapshot(
        self,
        session_id: str,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """Rollback session to a specific snapshot"""
        session = self.store.get_session(session_id)
        snapshots = self.store.get_snapshots(session_id)

        target_snapshot = None
        for snapshot in snapshots:
            if snapshot.id == snapshot_id:
                target_snapshot = snapshot
                break

        if not target_snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        # Get messages up to snapshot time
        all_messages = self.store.get_messages(session_id)
        snapshot_time = datetime.fromisoformat(target_snapshot.timestamp)

        messages_at_snapshot = [
            m for m in all_messages
            if datetime.fromisoformat(m.timestamp) <= snapshot_time
        ]

        return {
            "session": session,
            "messages": messages_at_snapshot,
            "agent_states": target_snapshot.agent_states,
            "system_state": target_snapshot.system_state,
            "snapshot": target_snapshot
        }


class SessionExporter:
    """Export and import sessions"""

    def __init__(self, session_store: SessionStore):
        """Initialize exporter"""
        self.store = session_store
        self.export_dir = Path("sessions/exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_session(
        self,
        session_id: str,
        format: str = "json",
        include_snapshots: bool = True
    ) -> Path:
        """Export session to file"""
        session = self.store.get_session(session_id)
        messages = self.store.get_messages(session_id)

        export_data = {
            "session": session.to_dict(),
            "messages": [m.to_dict() for m in messages]
        }

        if include_snapshots:
            snapshots = self.store.get_snapshots(session_id)
            export_data["snapshots"] = [s.to_dict() for s in snapshots]

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{session_id[:8]}_{timestamp}.{format}"
        filepath = self.export_dir / filename

        if format == "json":
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format == "json.gz":
            with gzip.open(str(filepath), 'wt') as f:
                json.dump(export_data, f, indent=2)
        elif format == "pickle":
            with open(filepath, 'wb') as f:
                pickle.dump(export_data, f)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return filepath

    def import_session(self, filepath: Path) -> Session:
        """Import session from file"""
        # Determine format from extension
        if filepath.suffix == ".gz":
            with gzip.open(str(filepath), 'rt') as f:
                data = json.load(f)
        elif filepath.suffix == ".json":
            with open(filepath, 'r') as f:
                data = json.load(f)
        elif filepath.suffix == ".pickle":
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

        # Create new session with new ID
        session_data = data["session"]
        new_session_id = str(uuid.uuid4())

        session = Session.from_dict(session_data)
        session.id = new_session_id
        session.status = SessionStatus.COMPLETED

        # Re-create session in store
        with self.store.lock:
            conn = sqlite3.connect(str(self.store.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sessions
                (id, started_at, ended_at, status, title, description,
                 message_count, agent_count, total_cost, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.started_at,
                session.ended_at,
                session.status.value,
                session.title,
                session.description,
                session.message_count,
                session.agent_count,
                session.total_cost,
                json.dumps(session.metadata)
            ))

            # Import messages
            for msg_data in data["messages"]:
                msg = Message.from_dict(msg_data)
                msg.id = str(uuid.uuid4())
                msg.session_id = new_session_id

                cursor.execute("""
                    INSERT INTO messages (id, session_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    msg.id,
                    msg.session_id,
                    msg.role.value,
                    msg.content,
                    msg.timestamp,
                    json.dumps(msg.metadata)
                ))

            # Import snapshots if present
            if "snapshots" in data:
                for snap_data in data["snapshots"]:
                    snap = SessionSnapshot.from_dict(snap_data)
                    snap.id = str(uuid.uuid4())
                    snap.session_id = new_session_id

                    cursor.execute("""
                        INSERT INTO snapshots
                        (id, session_id, snapshot_type, timestamp, message_count,
                         agent_states, system_state, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        snap.id,
                        snap.session_id,
                        snap.snapshot_type.value,
                        snap.timestamp,
                        snap.message_count,
                        json.dumps([s.to_dict() for s in snap.agent_states]),
                        json.dumps(snap.system_state),
                        snap.description
                    ))

            conn.commit()
            conn.close()

        return session


class SessionManager:
    """
    High-level session management interface.

    Combines all session features into a single convenient API.
    """

    def __init__(self, db_path: Path = None):
        """Initialize session manager"""
        self.store = SessionStore(db_path)
        self.recovery = RecoveryManager(self.store)
        self.exporter = SessionExporter(self.store)
        self.current_session: Optional[Session] = None
        self.auto_snapshot_interval = 100  # messages
        self.message_count_since_snapshot = 0

    def start_session(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Session:
        """Start a new session"""
        self.current_session = self.store.create_session(title, description)
        self.message_count_since_snapshot = 0
        return self.current_session

    def end_session(self, session_id: Optional[str] = None):
        """End a session"""
        if session_id:
            session = self.store.get_session(session_id)
        else:
            session = self.current_session

        if session:
            session.ended_at = datetime.now().isoformat()
            session.status = SessionStatus.COMPLETED
            self.store.update_session(session)

            if session == self.current_session:
                self.current_session = None

    def add_message(
        self,
        role: MessageRole,
        content: str,
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Add a message to current session"""
        if session_id:
            session = self.store.get_session(session_id)
        else:
            session = self.current_session

        if not session:
            raise ValueError("No active session")

        message = Message(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )

        self.store.add_message(message)
        self.message_count_since_snapshot += 1

        # Auto-snapshot
        if self.message_count_since_snapshot >= self.auto_snapshot_interval:
            self.create_auto_snapshot(session.id, [], {})
            self.message_count_since_snapshot = 0

    def create_auto_snapshot(
        self,
        session_id: str,
        agent_states: List[AgentState],
        system_state: Dict[str, Any]
    ):
        """Create automatic snapshot"""
        return self.recovery.create_recovery_point(
            session_id,
            agent_states,
            system_state
        )

    def create_checkpoint(
        self,
        description: str,
        agent_states: List[AgentState],
        system_state: Dict[str, Any],
        session_id: Optional[str] = None
    ):
        """Create manual checkpoint"""
        if session_id:
            sid = session_id
        else:
            sid = self.current_session.id

        return self.recovery.create_checkpoint(
            sid,
            agent_states,
            system_state,
            description
        )

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        limit: int = 50
    ) -> List[Session]:
        """List sessions"""
        return self.store.list_sessions(status, limit)

    def resume_session(self, session_id: str) -> Dict[str, Any]:
        """Resume a session"""
        recovery_data = self.recovery.recover_session(session_id)
        self.current_session = recovery_data["session"]
        return recovery_data

    def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get session conversation history"""
        return self.store.get_messages(session_id, limit)

    def export_current_session(self, format: str = "json") -> Path:
        """Export current session"""
        if not self.current_session:
            raise ValueError("No active session")

        return self.exporter.export_session(
            self.current_session.id,
            format,
            include_snapshots=True
        )
