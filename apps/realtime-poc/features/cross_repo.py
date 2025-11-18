#!/usr/bin/env python3
"""
Cross-Repository Agent Orchestration

Coordinates agents across multiple repositories, enabling complex workflows
that span different codebases. Manages dependencies, synchronization, and
cross-repo task execution.
"""

import json
import subprocess
import threading
import uuid
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class RepositoryStatus(Enum):
    """Repository status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"


class TaskStatus(Enum):
    """Cross-repo task status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_DEPENDENCY = "waiting_dependency"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Repository:
    """Represents a repository in the multi-repo setup"""

    def __init__(
        self,
        name: str,
        path: str,
        remote_url: Optional[str] = None,
        branch: str = "main",
    ):
        self.repo_id = str(uuid.uuid4())
        self.name = name
        self.path = Path(path)
        self.remote_url = remote_url
        self.branch = branch
        self.status = RepositoryStatus.INACTIVE
        self.metadata: Dict[str, Any] = {}
        self.agents: List[str] = []  # Agent names assigned to this repo

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "repo_id": self.repo_id,
            "name": self.name,
            "path": str(self.path),
            "remote_url": self.remote_url,
            "branch": self.branch,
            "status": self.status.value,
            "metadata": self.metadata,
            "agents": self.agents,
        }


class CrossRepoTask:
    """Task that spans multiple repositories"""

    def __init__(
        self,
        name: str,
        description: str,
        repositories: List[str],  # Repository names
        dependencies: Optional[List[str]] = None,  # Task IDs
    ):
        self.task_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.repositories = repositories
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.assigned_agent: Optional[str] = None
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "repositories": self.repositories,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "result": self.result,
            "error": self.error,
        }


class RepositoryRegistry:
    """Manages multiple repositories"""

    def __init__(self, registry_file: str = "cross_repo/registry.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.repositories: Dict[str, Repository] = {}
        self.lock = threading.Lock()
        self._load_registry()

    def _load_registry(self):
        """Load registry from file"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file) as f:
                    data = json.load(f)
                    for repo_data in data.get("repositories", []):
                        repo = Repository(
                            name=repo_data["name"],
                            path=repo_data["path"],
                            remote_url=repo_data.get("remote_url"),
                            branch=repo_data.get("branch", "main"),
                        )
                        repo.repo_id = repo_data["repo_id"]
                        repo.status = RepositoryStatus(repo_data.get("status", "inactive"))
                        repo.metadata = repo_data.get("metadata", {})
                        repo.agents = repo_data.get("agents", [])
                        self.repositories[repo.name] = repo
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")

    def _save_registry(self):
        """Save registry to file"""
        with self.lock:
            data = {
                "repositories": [repo.to_dict() for repo in self.repositories.values()],
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=2)

    def register_repository(
        self,
        name: str,
        path: str,
        remote_url: Optional[str] = None,
        branch: str = "main",
    ) -> Repository:
        """Register a repository"""
        if name in self.repositories:
            raise ValueError(f"Repository '{name}' already registered")

        repo = Repository(name=name, path=path, remote_url=remote_url, branch=branch)

        # Verify repository exists
        if not repo.path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {path}")

        # Check if it's a git repository
        if (repo.path / ".git").exists():
            repo.metadata["is_git"] = True
            repo.status = RepositoryStatus.ACTIVE
        else:
            repo.metadata["is_git"] = False
            repo.status = RepositoryStatus.ACTIVE

        self.repositories[name] = repo
        self._save_registry()

        return repo

    def unregister_repository(self, name: str):
        """Unregister a repository"""
        if name in self.repositories:
            del self.repositories[name]
            self._save_registry()

    def get_repository(self, name: str) -> Optional[Repository]:
        """Get repository by name"""
        return self.repositories.get(name)

    def list_repositories(self) -> List[Repository]:
        """List all repositories"""
        return list(self.repositories.values())

    def assign_agent(self, repo_name: str, agent_name: str):
        """Assign an agent to a repository"""
        repo = self.get_repository(repo_name)
        if repo and agent_name not in repo.agents:
            repo.agents.append(agent_name)
            self._save_registry()

    def get_repository_status(self, name: str) -> Dict:
        """Get repository status"""
        repo = self.get_repository(name)
        if not repo:
            return {"error": f"Repository '{name}' not found"}

        status = repo.to_dict()

        # Add git status if it's a git repo
        if repo.metadata.get("is_git"):
            try:
                # Get current branch
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=repo.path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                status["current_branch"] = result.stdout.strip()

                # Get uncommitted changes
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=repo.path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                status["uncommitted_changes"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            except Exception as e:
                status["git_error"] = str(e)

        return status


class DependencyResolver:
    """Resolves task dependencies across repositories"""

    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, task_id: str, depends_on: str):
        """Add task dependency"""
        self.dependency_graph[task_id].add(depends_on)

    def get_dependencies(self, task_id: str) -> Set[str]:
        """Get task dependencies"""
        return self.dependency_graph.get(task_id, set())

    def can_execute(self, task_id: str, completed_tasks: Set[str]) -> bool:
        """Check if task can be executed (all dependencies met)"""
        dependencies = self.get_dependencies(task_id)
        return dependencies.issubset(completed_tasks)

    def get_execution_order(self, task_ids: List[str]) -> List[List[str]]:
        """Get task execution order (topological sort)"""
        # Build reverse dependency graph
        dependents: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = {task_id: 0 for task_id in task_ids}

        for task_id in task_ids:
            for dep in self.dependency_graph.get(task_id, []):
                dependents[dep].add(task_id)
                in_degree[task_id] = in_degree.get(task_id, 0) + 1

        # Find tasks with no dependencies (can execute immediately)
        execution_order = []
        current_level = [tid for tid in task_ids if in_degree[tid] == 0]

        while current_level:
            execution_order.append(current_level)
            next_level = []

            for task_id in current_level:
                for dependent in dependents[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)

            current_level = next_level

        return execution_order


class CrossRepoOrchestrator:
    """Orchestrates tasks across multiple repositories"""

    def __init__(self, registry: Optional[RepositoryRegistry] = None):
        self.registry = registry or RepositoryRegistry()
        self.tasks: Dict[str, CrossRepoTask] = {}
        self.dependency_resolver = DependencyResolver()
        self.lock = threading.Lock()

    def create_task(
        self,
        name: str,
        description: str,
        repositories: List[str],
        dependencies: Optional[List[str]] = None,
    ) -> CrossRepoTask:
        """Create a cross-repo task"""
        # Validate repositories
        for repo_name in repositories:
            if not self.registry.get_repository(repo_name):
                raise ValueError(f"Repository '{repo_name}' not registered")

        task = CrossRepoTask(
            name=name,
            description=description,
            repositories=repositories,
            dependencies=dependencies,
        )

        with self.lock:
            self.tasks[task.task_id] = task

            # Register dependencies
            if dependencies:
                for dep_id in dependencies:
                    self.dependency_resolver.add_dependency(task.task_id, dep_id)

        return task

    def assign_task(self, task_id: str, agent_name: str):
        """Assign task to an agent"""
        task = self.tasks.get(task_id)
        if task:
            task.assigned_agent = agent_name

    def start_task(self, task_id: str) -> Dict:
        """Start task execution"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        # Check dependencies
        completed_tasks = {
            tid for tid, t in self.tasks.items() if t.status == TaskStatus.COMPLETED
        }

        if not self.dependency_resolver.can_execute(task_id, completed_tasks):
            task.status = TaskStatus.WAITING_DEPENDENCY
            return {
                "status": "waiting",
                "message": "Task waiting for dependencies",
                "dependencies": list(self.dependency_resolver.get_dependencies(task_id)),
            }

        # Start task
        task.status = TaskStatus.IN_PROGRESS
        task.start_time = datetime.now().isoformat()

        return {
            "status": "started",
            "task_id": task_id,
            "repositories": task.repositories,
        }

    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Complete a task"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.end_time = datetime.now().isoformat()
        task.result = result

        if success:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.FAILED
            task.error = error

    def get_task_status(self, task_id: str) -> Dict:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        return task.to_dict()

    def get_executable_tasks(self) -> List[str]:
        """Get tasks that can be executed now"""
        completed_tasks = {
            tid for tid, t in self.tasks.items() if t.status == TaskStatus.COMPLETED
        }

        executable = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                if self.dependency_resolver.can_execute(task_id, completed_tasks):
                    executable.append(task_id)

        return executable

    def get_execution_plan(self) -> List[List[str]]:
        """Get execution plan for all pending tasks"""
        pending_tasks = [
            tid
            for tid, task in self.tasks.items()
            if task.status in [TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCY]
        ]

        return self.dependency_resolver.get_execution_order(pending_tasks)

    def sync_repositories(self, repo_names: Optional[List[str]] = None) -> Dict:
        """Sync repositories with remote"""
        if repo_names is None:
            repo_names = [repo.name for repo in self.registry.list_repositories()]

        results = {}

        for repo_name in repo_names:
            repo = self.registry.get_repository(repo_name)
            if not repo:
                results[repo_name] = {"error": "Repository not found"}
                continue

            if not repo.metadata.get("is_git"):
                results[repo_name] = {"skipped": "Not a git repository"}
                continue

            repo.status = RepositoryStatus.SYNCING

            try:
                # Fetch from remote
                if repo.remote_url:
                    result = subprocess.run(
                        ["git", "fetch", "origin"],
                        cwd=repo.path,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode != 0:
                        raise RuntimeError(f"Fetch failed: {result.stderr}")

                # Get status
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=repo.path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                repo.status = RepositoryStatus.ACTIVE
                results[repo_name] = {
                    "status": "synced",
                    "uncommitted_changes": len(result.stdout.strip().split("\n"))
                    if result.stdout.strip()
                    else 0,
                }

            except Exception as e:
                repo.status = RepositoryStatus.ERROR
                results[repo_name] = {"error": str(e)}

        return results


class CrossRepoSession:
    """Manages interactive cross-repo workflows"""

    def __init__(
        self,
        registry: Optional[RepositoryRegistry] = None,
        orchestrator: Optional[CrossRepoOrchestrator] = None,
    ):
        self.session_id = str(uuid.uuid4())
        self.registry = registry or RepositoryRegistry()
        self.orchestrator = orchestrator or CrossRepoOrchestrator(self.registry)
        self.session_tasks: List[str] = []  # Task IDs created in this session

    def register_repositories(self, repo_configs: List[Dict]) -> List[Repository]:
        """Register multiple repositories"""
        repositories = []

        for config in repo_configs:
            repo = self.registry.register_repository(
                name=config["name"],
                path=config["path"],
                remote_url=config.get("remote_url"),
                branch=config.get("branch", "main"),
            )
            repositories.append(repo)

        return repositories

    def create_workflow(
        self,
        workflow_name: str,
        tasks: List[Dict],
    ) -> Dict:
        """Create a multi-task workflow"""
        created_tasks = []
        task_map = {}  # Map workflow task names to task IDs

        # Create tasks
        for task_config in tasks:
            # Resolve dependency IDs
            dep_names = task_config.get("dependencies", [])
            dep_ids = [task_map[name] for name in dep_names if name in task_map]

            task = self.orchestrator.create_task(
                name=task_config["name"],
                description=task_config["description"],
                repositories=task_config["repositories"],
                dependencies=dep_ids,
            )

            created_tasks.append(task)
            task_map[task_config["name"]] = task.task_id
            self.session_tasks.append(task.task_id)

        # Get execution plan
        execution_plan = self.orchestrator.get_execution_plan()

        return {
            "workflow_name": workflow_name,
            "session_id": self.session_id,
            "tasks_created": len(created_tasks),
            "task_ids": [t.task_id for t in created_tasks],
            "execution_plan": execution_plan,
        }

    def execute_next_tasks(self) -> List[Dict]:
        """Execute next available tasks"""
        executable = self.orchestrator.get_executable_tasks()

        # Filter to session tasks
        session_executable = [tid for tid in executable if tid in self.session_tasks]

        results = []
        for task_id in session_executable:
            result = self.orchestrator.start_task(task_id)
            results.append({
                "task_id": task_id,
                "result": result,
            })

        return results

    def get_session_status(self) -> Dict:
        """Get session status"""
        tasks = [self.orchestrator.tasks[tid] for tid in self.session_tasks]

        status_counts = defaultdict(int)
        for task in tasks:
            status_counts[task.status.value] += 1

        return {
            "session_id": self.session_id,
            "total_tasks": len(tasks),
            "status_breakdown": dict(status_counts),
            "executable_tasks": len(self.orchestrator.get_executable_tasks()),
            "repositories": len(self.registry.list_repositories()),
        }

    def get_task_details(self, task_id: str) -> Dict:
        """Get detailed task information"""
        return self.orchestrator.get_task_status(task_id)

    def sync_all_repositories(self) -> Dict:
        """Sync all registered repositories"""
        return self.orchestrator.sync_repositories()
