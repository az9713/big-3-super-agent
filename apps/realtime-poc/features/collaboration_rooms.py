#!/usr/bin/env python3
"""
Multi-Agent Collaboration Rooms

Enables multiple AI agents to work together in persistent shared workspaces
with coordinated task execution, shared context, and inter-agent communication.
"""

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class Task:
    """Represents a task in the collaboration room"""

    def __init__(
        self,
        description: str,
        assigned_to: str,
        dependencies: Optional[List[str]] = None,
    ):
        self.task_id = str(uuid.uuid4())
        self.description = description
        self.assigned_to = assigned_to
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, in_progress, completed, failed
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "dependencies": self.dependencies,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


class CollaborationRoom:
    """Represents a collaboration room with multiple agents"""

    def __init__(self, name: str, description: str, working_directory: str):
        self.room_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.working_directory = working_directory
        self.created_at = datetime.now().isoformat()
        self.status = "active"  # active, paused, completed, archived
        self.agents: List[Dict] = []
        self.shared_context = {
            "files_watched": [],
            "knowledge_base": {},
            "shared_findings": [],
            "decisions": [],
        }
        self.task_queue: List[Task] = []
        self.operator_log_path: Optional[Path] = None
        self.screenshots_dir: Optional[Path] = None
        self._lock = threading.Lock()

    def add_agent(
        self,
        agent_name: str,
        role: str,
        tool: str,
        specialization: str = "",
    ):
        """Add agent to room"""
        with self._lock:
            agent_info = {
                "agent_name": agent_name,
                "role": role,
                "tool": tool,
                "specialization": specialization,
                "status": "active",
                "current_task": None,
                "joined_at": datetime.now().isoformat(),
            }
            self.agents.append(agent_info)
            self.update_operator_log(
                f"**[System]** {agent_name} ({role}) joined the room"
            )

    def add_task(self, task: Task):
        """Add task to queue"""
        with self._lock:
            self.task_queue.append(task)

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks with no pending dependencies"""
        ready = []
        for task in self.task_queue:
            if task.status == "pending" and self._dependencies_met(task):
                ready.append(task)
        return ready

    def _dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies are completed"""
        for dep_id in task.dependencies:
            dep_task = self._get_task(dep_id)
            if not dep_task or dep_task.status != "completed":
                return False
        return True

    def _get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        for task in self.task_queue:
            if task.task_id == task_id:
                return task
        return None

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """Update task status"""
        with self._lock:
            task = self._get_task(task_id)
            if task:
                task.status = status
                if status == "in_progress" and not task.started_at:
                    task.started_at = datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    task.completed_at = datetime.now().isoformat()
                    task.result = result
                    task.error = error

    def broadcast_finding(self, agent_name: str, message: str, type: str = "info"):
        """Agent broadcasts finding to room"""
        with self._lock:
            finding = {
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "type": type,
                "message": message,
            }
            self.shared_context["shared_findings"].append(finding)
            self.update_operator_log(f"**[{agent_name}]** 📢 {message}")

    def record_decision(
        self,
        decision: str,
        rationale: str,
        participants: List[str],
    ):
        """Record a decision made by agents"""
        with self._lock:
            decision_record = {
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "rationale": rationale,
                "participants": participants,
            }
            self.shared_context["decisions"].append(decision_record)
            self.update_operator_log(
                f"**[Decision]** {decision}\n" +
                f"Rationale: {rationale}\n" +
                f"Participants: {', '.join(participants)}"
            )

    def update_operator_log(self, message: str):
        """Append to unified operator log"""
        if not self.operator_log_path:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        try:
            with open(self.operator_log_path, "a") as f:
                f.write(f"\n[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error updating operator log: {e}")

    def get_status(self) -> Dict:
        """Get room status summary"""
        with self._lock:
            return {
                "room_id": self.room_id,
                "name": self.name,
                "description": self.description,
                "status": self.status,
                "working_directory": self.working_directory,
                "agents": self.agents.copy(),
                "tasks": {
                    "completed": len([t for t in self.task_queue if t.status == "completed"]),
                    "in_progress": len([t for t in self.task_queue if t.status == "in_progress"]),
                    "pending": len([t for t in self.task_queue if t.status == "pending"]),
                    "failed": len([t for t in self.task_queue if t.status == "failed"]),
                },
                "recent_findings": self.shared_context["shared_findings"][-5:],
                "recent_decisions": self.shared_context["decisions"][-3:],
            }

    def to_dict(self) -> Dict:
        """Convert room to dictionary"""
        with self._lock:
            return {
                "room_id": self.room_id,
                "name": self.name,
                "description": self.description,
                "working_directory": self.working_directory,
                "created_at": self.created_at,
                "status": self.status,
                "agents": self.agents,
                "shared_context": self.shared_context,
                "task_queue": [t.to_dict() for t in self.task_queue],
                "operator_log": str(self.operator_log_path) if self.operator_log_path else None,
                "screenshots_dir": str(self.screenshots_dir) if self.screenshots_dir else None,
            }


class CollaborationRoomManager:
    """Manages collaboration rooms and agent coordination"""

    def __init__(self, base_dir: str = "apps/content-gen"):
        self.base_dir = Path(base_dir)
        self.rooms_dir = self.base_dir / "agents" / "collaboration_rooms"
        self.registry_path = self.rooms_dir / "registry.json"
        self.active_rooms: Dict[str, CollaborationRoom] = {}
        self._lock = threading.Lock()
        self._init_storage()

    def _init_storage(self):
        """Initialize storage directories"""
        self.rooms_dir.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self._save_registry()

    def _load_registry(self) -> Dict:
        """Load registry from disk"""
        try:
            with open(self.registry_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_registry(self):
        """Save registry to disk"""
        with self._lock:
            registry = {
                name: {
                    "room_id": room.room_id,
                    "name": room.name,
                    "status": room.status,
                    "created_at": room.created_at,
                    "working_directory": room.working_directory,
                }
                for name, room in self.active_rooms.items()
            }
            with open(self.registry_path, "w") as f:
                json.dump(registry, f, indent=2)

    def create_room(
        self,
        name: str,
        description: str,
        working_directory: Optional[str] = None,
    ) -> Dict:
        """Create new collaboration room"""
        if working_directory is None:
            working_directory = str(self.base_dir)

        with self._lock:
            if name in self.active_rooms:
                return {"error": f"Room '{name}' already exists"}

            room = CollaborationRoom(name, description, working_directory)

            # Create room directory structure
            room_dir = self.rooms_dir / name
            room_dir.mkdir(parents=True, exist_ok=True)
            (room_dir / "screenshots").mkdir(exist_ok=True)

            # Create unified operator log
            operator_log = room_dir / "operator_log.md"
            operator_log.write_text(
                f"# Collaboration Room: {name}\n\n"
                f"**Description**: {description}\n"
                f"**Created**: {room.created_at}\n"
                f"**Working Directory**: {working_directory}\n\n"
                f"---\n\n"
            )
            room.operator_log_path = operator_log
            room.screenshots_dir = room_dir / "screenshots"

            self.active_rooms[name] = room
            self._save_registry()

            return {
                "status": "created",
                "room_id": room.room_id,
                "name": name,
                "working_directory": working_directory,
            }

    def add_agent_to_room(
        self,
        room_name: str,
        agent_name: str,
        role: str,
        tool: str,
        specialization: str = "",
    ) -> Dict:
        """Add agent to room"""
        with self._lock:
            if room_name not in self.active_rooms:
                return {"error": f"Room '{room_name}' not found"}

            room = self.active_rooms[room_name]
            room.add_agent(agent_name, role, tool, specialization)
            self._save_registry()

            return {
                "status": "added",
                "room_name": room_name,
                "agent_name": agent_name,
            }

    def get_room(self, room_name: str) -> Optional[CollaborationRoom]:
        """Get room by name"""
        return self.active_rooms.get(room_name)

    def room_command(
        self,
        room_name: str,
        task_description: str,
        assign_to: Optional[str] = None,
    ) -> Dict:
        """Add task to room"""
        with self._lock:
            if room_name not in self.active_rooms:
                return {"error": f"Room '{room_name}' not found"}

            room = self.active_rooms[room_name]

            if not room.agents:
                return {"error": "No agents in room"}

            # If no specific agent, assign to first agent
            if not assign_to:
                assign_to = room.agents[0]["agent_name"]

            # Create task
            task = Task(
                description=task_description,
                assigned_to=assign_to,
            )
            room.add_task(task)

            room.update_operator_log(
                f"**[Task Created]** Assigned to {assign_to}\n" +
                f"Description: {task_description}\n" +
                f"Task ID: {task.task_id}"
            )

            return {
                "status": "task_created",
                "task_id": task.task_id,
                "assigned_to": assign_to,
                "description": task_description,
            }

    def get_room_status(self, room_name: str) -> Dict:
        """Get room status"""
        with self._lock:
            if room_name not in self.active_rooms:
                return {"error": f"Room '{room_name}' not found"}

            room = self.active_rooms[room_name]
            return room.get_status()

    def archive_room(self, room_name: str) -> Dict:
        """Archive a room"""
        with self._lock:
            if room_name not in self.active_rooms:
                return {"error": f"Room '{room_name}' not found"}

            room = self.active_rooms[room_name]
            room.status = "archived"
            room.update_operator_log("**[System]** Room archived")

            # Save final state
            room_dir = self.rooms_dir / room_name
            state_file = room_dir / "final_state.json"
            with open(state_file, "w") as f:
                json.dump(room.to_dict(), f, indent=2)

            # Remove from active rooms
            del self.active_rooms[room_name]
            self._save_registry()

            return {
                "status": "archived",
                "room_name": room_name,
                "operator_log": str(room.operator_log_path),
                "final_state": str(state_file),
            }

    def list_rooms(self) -> List[Dict]:
        """List all active rooms"""
        with self._lock:
            return [
                {
                    "name": name,
                    "room_id": room.room_id,
                    "status": room.status,
                    "agents": len(room.agents),
                    "tasks": len(room.task_queue),
                    "created_at": room.created_at,
                }
                for name, room in self.active_rooms.items()
            ]
