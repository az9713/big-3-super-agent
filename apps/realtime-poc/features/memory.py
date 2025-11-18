#!/usr/bin/env python3
"""
Agent Memory & Learning System

Tracks agent interactions, learns from patterns, and builds a searchable
knowledge base to improve performance over time. Enables agents to remember
past solutions and apply learned patterns to new problems.
"""

import hashlib
import json
import sqlite3
import threading
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MemoryStore:
    """Persistent storage for agent interactions and outcomes"""

    def __init__(self, db_path: str = "memory/agent_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Create database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    approach TEXT,
                    outcome TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    duration_seconds REAL,
                    error_message TEXT,
                    context TEXT,
                    tags TEXT
                );

                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    relevance_score REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_interactions_agent
                    ON interactions(agent_name);
                CREATE INDEX IF NOT EXISTS idx_interactions_task_type
                    ON interactions(task_type);
                CREATE INDEX IF NOT EXISTS idx_interactions_success
                    ON interactions(success);
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp
                    ON interactions(timestamp);

                CREATE INDEX IF NOT EXISTS idx_patterns_type
                    ON patterns(pattern_type);
                CREATE INDEX IF NOT EXISTS idx_patterns_confidence
                    ON patterns(confidence);

                CREATE INDEX IF NOT EXISTS idx_knowledge_category
                    ON knowledge_entries(category);
                CREATE INDEX IF NOT EXISTS idx_knowledge_relevance
                    ON knowledge_entries(relevance_score);
            """)

    def store_interaction(
        self,
        agent_name: str,
        task_type: str,
        task_description: str,
        approach: str,
        outcome: str,
        success: bool,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        context: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Store an agent interaction"""
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO interactions (
                        id, timestamp, agent_name, task_type, task_description,
                        approach, outcome, success, duration_seconds, error_message,
                        context, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interaction_id,
                        timestamp,
                        agent_name,
                        task_type,
                        task_description,
                        approach,
                        outcome,
                        1 if success else 0,
                        duration_seconds,
                        error_message,
                        json.dumps(context) if context else None,
                        json.dumps(tags) if tags else None,
                    ),
                )

        return interaction_id

    def get_interactions(
        self,
        agent_name: Optional[str] = None,
        task_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Retrieve interactions with optional filters"""
        query = "SELECT * FROM interactions WHERE 1=1"
        params = []

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)

        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        interactions = []
        for row in rows:
            interaction = dict(row)
            interaction["success"] = bool(interaction["success"])
            if interaction["context"]:
                interaction["context"] = json.loads(interaction["context"])
            if interaction["tags"]:
                interaction["tags"] = json.loads(interaction["tags"])
            interactions.append(interaction)

        return interactions

    def store_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict,
        success_count: int = 0,
        failure_count: int = 0,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store a learned pattern"""
        pattern_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Calculate confidence
        total = success_count + failure_count
        confidence = success_count / total if total > 0 else 0.0

        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO patterns (
                        id, pattern_type, pattern_data, success_count,
                        failure_count, confidence, first_seen, last_seen, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pattern_id,
                        pattern_type,
                        json.dumps(pattern_data),
                        success_count,
                        failure_count,
                        confidence,
                        timestamp,
                        timestamp,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

        return pattern_id

    def update_pattern(
        self,
        pattern_id: str,
        success_increment: int = 0,
        failure_increment: int = 0,
    ):
        """Update pattern success/failure counts"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Get current counts
                cursor = conn.execute(
                    "SELECT success_count, failure_count FROM patterns WHERE id = ?",
                    (pattern_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return

                success_count = row[0] + success_increment
                failure_count = row[1] + failure_increment
                total = success_count + failure_count
                confidence = success_count / total if total > 0 else 0.0

                # Update pattern
                conn.execute(
                    """
                    UPDATE patterns
                    SET success_count = ?, failure_count = ?,
                        confidence = ?, last_seen = ?
                    WHERE id = ?
                    """,
                    (
                        success_count,
                        failure_count,
                        confidence,
                        datetime.now().isoformat(),
                        pattern_id,
                    ),
                )

    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> List[Dict]:
        """Retrieve learned patterns"""
        query = "SELECT * FROM patterns WHERE confidence >= ?"
        params = [min_confidence]

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY confidence DESC, success_count DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        patterns = []
        for row in rows:
            pattern = dict(row)
            pattern["pattern_data"] = json.loads(pattern["pattern_data"])
            if pattern["metadata"]:
                pattern["metadata"] = json.loads(pattern["metadata"])
            patterns.append(pattern)

        return patterns

    def store_knowledge(
        self,
        category: str,
        title: str,
        content: str,
        source: Optional[str] = None,
        relevance_score: float = 1.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store knowledge entry"""
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO knowledge_entries (
                        id, category, title, content, source, relevance_score,
                        created_at, updated_at, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        category,
                        title,
                        content,
                        source,
                        relevance_score,
                        timestamp,
                        timestamp,
                        json.dumps(tags) if tags else None,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

        return entry_id

    def search_knowledge(
        self,
        category: Optional[str] = None,
        search_term: Optional[str] = None,
        min_relevance: float = 0.0,
        limit: int = 20,
    ) -> List[Dict]:
        """Search knowledge base"""
        query = "SELECT * FROM knowledge_entries WHERE relevance_score >= ?"
        params = [min_relevance]

        if category:
            query += " AND category = ?"
            params.append(category)

        if search_term:
            query += " AND (title LIKE ? OR content LIKE ?)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])

        query += " ORDER BY relevance_score DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        entries = []
        for row in rows:
            entry = dict(row)
            if entry["tags"]:
                entry["tags"] = json.loads(entry["tags"])
            if entry["metadata"]:
                entry["metadata"] = json.loads(entry["metadata"])
            entries.append(entry)

        return entries


class PatternLearner:
    """Identifies and learns patterns from agent interactions"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store

    def learn_from_interactions(
        self,
        task_type: Optional[str] = None,
        min_occurrences: int = 3,
    ) -> List[Dict]:
        """Analyze interactions and identify patterns"""
        # Get successful and failed interactions
        successful = self.memory.get_interactions(
            task_type=task_type, success=True, limit=500
        )
        failed = self.memory.get_interactions(
            task_type=task_type, success=False, limit=500
        )

        patterns = []

        # Pattern 1: Successful approaches for task types
        approach_patterns = self._identify_approach_patterns(successful, min_occurrences)
        patterns.extend(approach_patterns)

        # Pattern 2: Common failure causes
        failure_patterns = self._identify_failure_patterns(failed, min_occurrences)
        patterns.extend(failure_patterns)

        # Pattern 3: Time-based patterns (fast vs slow tasks)
        duration_patterns = self._identify_duration_patterns(successful, min_occurrences)
        patterns.extend(duration_patterns)

        return patterns

    def _identify_approach_patterns(
        self,
        interactions: List[Dict],
        min_occurrences: int,
    ) -> List[Dict]:
        """Identify common successful approaches"""
        # Group by task_type and approach
        approach_counts = defaultdict(lambda: defaultdict(int))

        for interaction in interactions:
            task_type = interaction["task_type"]
            approach = interaction.get("approach", "unknown")
            approach_counts[task_type][approach] += 1

        patterns = []
        for task_type, approaches in approach_counts.items():
            for approach, count in approaches.items():
                if count >= min_occurrences:
                    # Store pattern
                    pattern_id = self.memory.store_pattern(
                        pattern_type="successful_approach",
                        pattern_data={
                            "task_type": task_type,
                            "approach": approach,
                            "description": f"Use '{approach}' for {task_type} tasks",
                        },
                        success_count=count,
                        failure_count=0,
                        metadata={"min_occurrences": min_occurrences},
                    )

                    patterns.append({
                        "pattern_id": pattern_id,
                        "type": "successful_approach",
                        "task_type": task_type,
                        "approach": approach,
                        "occurrences": count,
                    })

        return patterns

    def _identify_failure_patterns(
        self,
        interactions: List[Dict],
        min_occurrences: int,
    ) -> List[Dict]:
        """Identify common failure causes"""
        # Group by error message keywords
        error_keywords = defaultdict(lambda: defaultdict(list))

        for interaction in interactions:
            error_msg = interaction.get("error_message", "")
            if not error_msg:
                continue

            # Extract error type (first word)
            error_type = error_msg.split(":")[0] if ":" in error_msg else error_msg.split()[0]
            task_type = interaction["task_type"]

            error_keywords[task_type][error_type].append(interaction)

        patterns = []
        for task_type, errors in error_keywords.items():
            for error_type, occurrences in errors.items():
                if len(occurrences) >= min_occurrences:
                    # Store pattern
                    pattern_id = self.memory.store_pattern(
                        pattern_type="common_failure",
                        pattern_data={
                            "task_type": task_type,
                            "error_type": error_type,
                            "description": f"Watch out for '{error_type}' in {task_type} tasks",
                            "prevention": "Add validation before execution",
                        },
                        success_count=0,
                        failure_count=len(occurrences),
                        metadata={"min_occurrences": min_occurrences},
                    )

                    patterns.append({
                        "pattern_id": pattern_id,
                        "type": "common_failure",
                        "task_type": task_type,
                        "error_type": error_type,
                        "occurrences": len(occurrences),
                    })

        return patterns

    def _identify_duration_patterns(
        self,
        interactions: List[Dict],
        min_occurrences: int,
    ) -> List[Dict]:
        """Identify time-based patterns"""
        # Group by task_type and calculate average duration
        duration_groups = defaultdict(list)

        for interaction in interactions:
            duration = interaction.get("duration_seconds")
            if duration is None:
                continue

            task_type = interaction["task_type"]
            duration_groups[task_type].append(duration)

        patterns = []
        for task_type, durations in duration_groups.items():
            if len(durations) < min_occurrences:
                continue

            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)

            # Classify as fast/medium/slow
            if avg_duration < 5:
                speed_class = "fast"
            elif avg_duration < 30:
                speed_class = "medium"
            else:
                speed_class = "slow"

            # Store pattern
            pattern_id = self.memory.store_pattern(
                pattern_type="duration_pattern",
                pattern_data={
                    "task_type": task_type,
                    "speed_class": speed_class,
                    "avg_duration": avg_duration,
                    "min_duration": min_duration,
                    "max_duration": max_duration,
                    "description": f"{task_type} tasks typically take {avg_duration:.1f}s ({speed_class})",
                },
                success_count=len(durations),
                failure_count=0,
                metadata={"sample_size": len(durations)},
            )

            patterns.append({
                "pattern_id": pattern_id,
                "type": "duration_pattern",
                "task_type": task_type,
                "speed_class": speed_class,
                "avg_duration": avg_duration,
            })

        return patterns

    def get_recommendations(self, task_type: str, context: Optional[Dict] = None) -> List[Dict]:
        """Get pattern-based recommendations for a task"""
        recommendations = []

        # Get successful approach patterns
        approach_patterns = self.memory.get_patterns(
            pattern_type="successful_approach",
            min_confidence=0.7,
        )

        for pattern in approach_patterns:
            if pattern["pattern_data"]["task_type"] == task_type:
                recommendations.append({
                    "type": "approach",
                    "priority": "high",
                    "confidence": pattern["confidence"],
                    "recommendation": pattern["pattern_data"]["description"],
                    "details": pattern["pattern_data"],
                })

        # Get failure patterns to avoid
        failure_patterns = self.memory.get_patterns(
            pattern_type="common_failure",
        )

        for pattern in failure_patterns:
            if pattern["pattern_data"]["task_type"] == task_type:
                recommendations.append({
                    "type": "warning",
                    "priority": "medium",
                    "confidence": 1.0,  # Failures are always relevant
                    "recommendation": pattern["pattern_data"]["description"],
                    "prevention": pattern["pattern_data"].get("prevention", ""),
                })

        # Get duration expectations
        duration_patterns = self.memory.get_patterns(
            pattern_type="duration_pattern",
        )

        for pattern in duration_patterns:
            if pattern["pattern_data"]["task_type"] == task_type:
                recommendations.append({
                    "type": "expectation",
                    "priority": "low",
                    "confidence": pattern["confidence"],
                    "recommendation": pattern["pattern_data"]["description"],
                })

        # Sort by priority and confidence
        priority_map = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(
            key=lambda x: (priority_map[x["priority"]], x["confidence"]),
            reverse=True,
        )

        return recommendations


class KnowledgeBase:
    """Searchable repository of learned knowledge"""

    def __init__(self, memory_store: MemoryStore):
        self.memory = memory_store

    def add_knowledge(
        self,
        category: str,
        title: str,
        content: str,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add knowledge entry"""
        return self.memory.store_knowledge(
            category=category,
            title=title,
            content=content,
            source=source,
            tags=tags,
        )

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search knowledge base"""
        return self.memory.search_knowledge(
            category=category,
            search_term=query,
            limit=limit,
        )

    def get_related(
        self,
        category: str,
        limit: int = 5,
    ) -> List[Dict]:
        """Get knowledge entries for a category"""
        return self.memory.search_knowledge(
            category=category,
            limit=limit,
        )

    def extract_knowledge_from_interactions(self, min_success_rate: float = 0.8):
        """Extract knowledge from successful interaction patterns"""
        # Get all interactions
        interactions = self.memory.get_interactions(limit=1000)

        # Group by task_type
        task_groups = defaultdict(list)
        for interaction in interactions:
            task_groups[interaction["task_type"]].append(interaction)

        # Extract knowledge for each task type
        for task_type, task_interactions in task_groups.items():
            if len(task_interactions) < 5:
                continue

            successful = [i for i in task_interactions if i["success"]]
            success_rate = len(successful) / len(task_interactions)

            if success_rate >= min_success_rate and len(successful) >= 3:
                # Extract common approaches
                approaches = defaultdict(int)
                for interaction in successful:
                    approach = interaction.get("approach", "")
                    if approach:
                        approaches[approach] += 1

                # Find most common approach
                if approaches:
                    best_approach = max(approaches.items(), key=lambda x: x[1])
                    approach_name, count = best_approach

                    # Create knowledge entry
                    self.add_knowledge(
                        category=task_type,
                        title=f"Best Practice for {task_type}",
                        content=f"Based on {count} successful executions ({success_rate*100:.1f}% success rate), "
                        + f"the recommended approach is: {approach_name}",
                        source="interaction_analysis",
                        tags=["best_practice", task_type, "high_confidence"],
                    )


class LearningSession:
    """Manages interactive learning and knowledge retrieval"""

    def __init__(self, memory_store: Optional[MemoryStore] = None):
        self.memory = memory_store or MemoryStore()
        self.pattern_learner = PatternLearner(self.memory)
        self.knowledge_base = KnowledgeBase(self.memory)
        self.session_id = str(uuid.uuid4())
        self.session_context: Dict[str, Any] = {}

    def record_interaction(
        self,
        agent_name: str,
        task_type: str,
        task_description: str,
        approach: str,
        outcome: str,
        success: bool,
        duration_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Record an agent interaction"""
        interaction_id = self.memory.store_interaction(
            agent_name=agent_name,
            task_type=task_type,
            task_description=task_description,
            approach=approach,
            outcome=outcome,
            success=success,
            duration_seconds=duration_seconds,
            error_message=error_message,
            context=self.session_context,
            tags=tags,
        )

        # Update session context
        self.session_context["last_interaction_id"] = interaction_id
        self.session_context["last_task_type"] = task_type

        return interaction_id

    def get_recommendations(
        self,
        task_type: str,
        include_knowledge: bool = True,
    ) -> Dict:
        """Get recommendations for a task"""
        # Get pattern-based recommendations
        pattern_recs = self.pattern_learner.get_recommendations(
            task_type=task_type,
            context=self.session_context,
        )

        result = {
            "task_type": task_type,
            "pattern_recommendations": pattern_recs,
        }

        # Get related knowledge
        if include_knowledge:
            knowledge = self.knowledge_base.get_related(
                category=task_type,
                limit=5,
            )
            result["knowledge_entries"] = knowledge

        return result

    def learn_patterns(
        self,
        task_type: Optional[str] = None,
        min_occurrences: int = 3,
    ) -> List[Dict]:
        """Learn patterns from interactions"""
        return self.pattern_learner.learn_from_interactions(
            task_type=task_type,
            min_occurrences=min_occurrences,
        )

    def add_knowledge(
        self,
        category: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add knowledge to the knowledge base"""
        return self.knowledge_base.add_knowledge(
            category=category,
            title=title,
            content=content,
            source=f"session_{self.session_id}",
            tags=tags,
        )

    def search_knowledge(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search the knowledge base"""
        return self.knowledge_base.search(query, category=category)

    def get_session_stats(self) -> Dict:
        """Get statistics for current session"""
        # Get recent interactions
        recent = self.memory.get_interactions(limit=100)

        # Calculate stats
        total = len(recent)
        successful = len([i for i in recent if i["success"]])
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0

        # Get pattern counts
        patterns = self.memory.get_patterns(limit=1000)
        pattern_types = defaultdict(int)
        for pattern in patterns:
            pattern_types[pattern["pattern_type"]] += 1

        # Get knowledge count
        knowledge = self.memory.search_knowledge(limit=1000)

        return {
            "session_id": self.session_id,
            "total_interactions": total,
            "successful_interactions": successful,
            "failed_interactions": failed,
            "success_rate": round(success_rate, 2),
            "patterns_learned": len(patterns),
            "pattern_types": dict(pattern_types),
            "knowledge_entries": len(knowledge),
        }
