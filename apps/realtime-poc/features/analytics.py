#!/usr/bin/env python3
"""
Agent Performance Analytics & Optimization Dashboard

Provides comprehensive metrics, insights, and AI-powered recommendations
for optimizing agent usage, costs, and performance.
"""

import json
import sqlite3
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MetricsDatabase:
    """SQLite database for storing metrics"""

    def __init__(self, db_path: str = "analytics/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS task_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                agent_name TEXT,
                agent_tool TEXT,
                task_type TEXT,
                task_description TEXT,
                project TEXT,
                user_id TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                duration_seconds INTEGER,
                status TEXT,
                error_message TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0,
                session_id TEXT,
                room_id TEXT,
                macro_id TEXT
            );

            CREATE TABLE IF NOT EXISTS agents (
                name TEXT PRIMARY KEY,
                tool TEXT,
                role TEXT,
                created_at TIMESTAMP,
                deleted_at TIMESTAMP,
                total_tasks_completed INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                avg_task_duration_seconds INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS daily_summaries (
                date DATE PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                total_duration_seconds INTEGER DEFAULT 0,
                unique_agents INTEGER DEFAULT 0,
                unique_projects INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                priority TEXT,
                description TEXT,
                estimated_savings_seconds INTEGER DEFAULT 0,
                estimated_savings_usd REAL DEFAULT 0.0,
                created_at TIMESTAMP,
                accepted_at TIMESTAMP,
                dismissed_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_task_started_at ON task_executions(started_at);
            CREATE INDEX IF NOT EXISTS idx_task_status ON task_executions(status);
            CREATE INDEX IF NOT EXISTS idx_task_agent ON task_executions(agent_name);
            CREATE INDEX IF NOT EXISTS idx_task_type ON task_executions(task_type);
        """)
        self.conn.commit()

    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute query with thread safety"""
        with self._lock:
            return self.conn.execute(query, params)

    def commit(self):
        """Commit transaction"""
        with self._lock:
            self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class MetricsCollector:
    """Collects and stores metrics from agent executions"""

    def __init__(self, db_path: str = "analytics/metrics.db"):
        self.db = MetricsDatabase(db_path)

    def track_task_start(
        self,
        task_id: str,
        agent_name: str,
        agent_tool: str,
        task_type: str,
        task_description: str,
        project: str = "default",
        session_id: str = "",
        room_id: str = "",
        macro_id: str = "",
    ):
        """Record task start"""
        self.db.execute(
            """
            INSERT OR REPLACE INTO task_executions
            (task_id, agent_name, agent_tool, task_type, task_description,
             project, started_at, status, session_id, room_id, macro_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?, ?)
            """,
            (task_id, agent_name, agent_tool, task_type, task_description,
             project, datetime.now(), session_id, room_id, macro_id),
        )
        self.db.commit()

    def track_task_end(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
    ):
        """Record task completion"""
        # Get start time to calculate duration
        row = self.db.execute(
            "SELECT started_at FROM task_executions WHERE task_id = ?",
            (task_id,),
        ).fetchone()

        duration_seconds = 0
        if row:
            start_time = datetime.fromisoformat(row["started_at"])
            duration_seconds = int((datetime.now() - start_time).total_seconds())

        total_tokens = prompt_tokens + completion_tokens

        self.db.execute(
            """
            UPDATE task_executions
            SET completed_at = ?,
                duration_seconds = ?,
                status = ?,
                error_message = ?,
                prompt_tokens = ?,
                completion_tokens = ?,
                total_tokens = ?,
                cost_usd = ?
            WHERE task_id = ?
            """,
            (datetime.now(), duration_seconds, status, error_message,
             prompt_tokens, completion_tokens, total_tokens, cost_usd, task_id),
        )
        self.db.commit()

        # Update daily summary
        self._update_daily_summary()

    def _update_daily_summary(self):
        """Update daily summary statistics"""
        today = datetime.now().date()

        # Get today's stats
        stats = self.db.execute(
            """
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_tasks,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
                SUM(cost_usd) as total_cost,
                SUM(duration_seconds) as total_duration,
                COUNT(DISTINCT agent_name) as unique_agents,
                COUNT(DISTINCT project) as unique_projects
            FROM task_executions
            WHERE DATE(started_at) = ?
            """,
            (today,),
        ).fetchone()

        self.db.execute(
            """
            INSERT OR REPLACE INTO daily_summaries
            (date, total_tasks, successful_tasks, failed_tasks, total_cost_usd,
             total_duration_seconds, unique_agents, unique_projects)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (today, stats["total_tasks"], stats["successful_tasks"],
             stats["failed_tasks"], stats["total_cost"] or 0.0,
             stats["total_duration"] or 0, stats["unique_agents"],
             stats["unique_projects"]),
        )
        self.db.commit()

    def get_metrics(
        self,
        time_period: str = "today",
        metric_type: str = "all",
    ) -> Dict:
        """Query metrics"""
        if time_period == "today":
            start_date = datetime.now().date()
        elif time_period == "week":
            start_date = datetime.now().date() - timedelta(days=7)
        elif time_period == "month":
            start_date = datetime.now().date() - timedelta(days=30)
        else:
            start_date = datetime.now().date()

        if metric_type == "cost":
            return self._get_cost_metrics(start_date)
        elif metric_type == "performance":
            return self._get_performance_metrics(start_date)
        elif metric_type == "tasks":
            return self._get_task_metrics(start_date)
        else:
            return {
                "cost": self._get_cost_metrics(start_date),
                "performance": self._get_performance_metrics(start_date),
                "tasks": self._get_task_metrics(start_date),
            }

    def _get_cost_metrics(self, start_date) -> Dict:
        """Get cost-related metrics"""
        total_cost = self.db.execute(
            """
            SELECT SUM(cost_usd) as total
            FROM task_executions
            WHERE DATE(started_at) >= ?
            """,
            (start_date,),
        ).fetchone()["total"] or 0.0

        by_agent_type = self.db.execute(
            """
            SELECT agent_tool, SUM(cost_usd) as cost, COUNT(*) as tasks
            FROM task_executions
            WHERE DATE(started_at) >= ?
            GROUP BY agent_tool
            ORDER BY cost DESC
            """,
            (start_date,),
        ).fetchall()

        by_task_type = self.db.execute(
            """
            SELECT task_type, SUM(cost_usd) as cost, COUNT(*) as tasks
            FROM task_executions
            WHERE DATE(started_at) >= ?
            GROUP BY task_type
            ORDER BY cost DESC
            """,
            (start_date,),
        ).fetchall()

        by_project = self.db.execute(
            """
            SELECT project, SUM(cost_usd) as cost, COUNT(*) as tasks
            FROM task_executions
            WHERE DATE(started_at) >= ?
            GROUP BY project
            ORDER BY cost DESC
            """,
            (start_date,),
        ).fetchall()

        return {
            "total_cost": round(total_cost, 2),
            "by_agent_type": [dict(row) for row in by_agent_type],
            "by_task_type": [dict(row) for row in by_task_type],
            "by_project": [dict(row) for row in by_project],
        }

    def _get_performance_metrics(self, start_date) -> Dict:
        """Get performance-related metrics"""
        avg_duration_by_type = self.db.execute(
            """
            SELECT task_type,
                   AVG(duration_seconds) as avg_duration,
                   COUNT(*) as task_count
            FROM task_executions
            WHERE DATE(started_at) >= ? AND status = 'completed'
            GROUP BY task_type
            ORDER BY avg_duration DESC
            """,
            (start_date,),
        ).fetchall()

        success_rate_by_type = self.db.execute(
            """
            SELECT task_type,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                   COUNT(*) as total_tasks
            FROM task_executions
            WHERE DATE(started_at) >= ?
            GROUP BY task_type
            HAVING COUNT(*) >= 3
            ORDER BY success_rate DESC
            """,
            (start_date,),
        ).fetchall()

        agent_efficiency = self.db.execute(
            """
            SELECT agent_name,
                   COUNT(*) * 3600.0 / SUM(duration_seconds) as tasks_per_hour,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                   COUNT(*) as total_tasks
            FROM task_executions
            WHERE DATE(started_at) >= ? AND duration_seconds > 0
            GROUP BY agent_name
            HAVING COUNT(*) >= 3
            ORDER BY tasks_per_hour DESC
            """,
            (start_date,),
        ).fetchall()

        failed_tasks = self.db.execute(
            """
            SELECT task_type, error_message, COUNT(*) as count
            FROM task_executions
            WHERE DATE(started_at) >= ? AND status = 'failed'
            GROUP BY task_type, error_message
            ORDER BY count DESC
            LIMIT 10
            """,
            (start_date,),
        ).fetchall()

        return {
            "avg_duration_by_type": [dict(row) for row in avg_duration_by_type],
            "success_rate_by_type": [dict(row) for row in success_rate_by_type],
            "agent_efficiency": [dict(row) for row in agent_efficiency],
            "failed_tasks": [dict(row) for row in failed_tasks],
        }

    def _get_task_metrics(self, start_date) -> Dict:
        """Get task-related metrics"""
        total_tasks = self.db.execute(
            "SELECT COUNT(*) as count FROM task_executions WHERE DATE(started_at) >= ?",
            (start_date,),
        ).fetchone()["count"]

        completed_tasks = self.db.execute(
            "SELECT COUNT(*) as count FROM task_executions WHERE DATE(started_at) >= ? AND status = 'completed'",
            (start_date,),
        ).fetchone()["count"]

        failed_tasks = self.db.execute(
            "SELECT COUNT(*) as count FROM task_executions WHERE DATE(started_at) >= ? AND status = 'failed'",
            (start_date,),
        ).fetchone()["count"]

        avg_duration = self.db.execute(
            "SELECT AVG(duration_seconds) as avg FROM task_executions WHERE DATE(started_at) >= ? AND status = 'completed'",
            (start_date,),
        ).fetchone()["avg"] or 0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": round(completed_tasks * 100.0 / total_tasks, 1) if total_tasks > 0 else 0,
            "avg_duration_seconds": round(avg_duration, 1),
        }


class RecommendationsEngine:
    """Generate optimization recommendations based on metrics"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def generate_recommendations(self) -> List[Dict]:
        """Analyze metrics and generate recommendations"""
        recommendations = []

        # Detect macro opportunities
        recommendations.extend(self._detect_macro_opportunities())

        # Analyze agent performance
        recommendations.extend(self._analyze_agent_performance())

        # Cost optimization
        recommendations.extend(self._cost_optimization())

        # Save to database
        for rec in recommendations:
            self.metrics.db.execute(
                """
                INSERT INTO recommendations
                (type, priority, description, estimated_savings_seconds,
                 estimated_savings_usd, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (rec["type"], rec["priority"], rec["description"],
                 rec.get("estimated_savings_seconds", 0),
                 rec.get("estimated_savings_usd", 0.0),
                 datetime.now()),
            )
        self.metrics.db.commit()

        return recommendations

    def _detect_macro_opportunities(self) -> List[Dict]:
        """Find repeated command sequences"""
        # Query for repeated task sequences
        sequences = self.metrics.db.execute("""
            SELECT
                GROUP_CONCAT(task_type, ' -> ') as pattern,
                COUNT(*) as times_used,
                AVG(total_duration) as avg_duration,
                SUM(total_cost) as total_cost
            FROM (
                SELECT
                    session_id,
                    task_type,
                    SUM(duration_seconds) as total_duration,
                    SUM(cost_usd) as total_cost
                FROM task_executions
                WHERE started_at >= date('now', '-7 days')
                  AND session_id != ''
                GROUP BY session_id, task_type
            )
            GROUP BY session_id
            HAVING COUNT(*) >= 3
        """).fetchall()

        recommendations = []
        # Count pattern frequencies
        pattern_counts = defaultdict(list)
        for seq in sequences:
            pattern = seq["pattern"]
            pattern_counts[pattern].append({
                "times_used": seq["times_used"],
                "avg_duration": seq["avg_duration"] or 0,
                "total_cost": seq["total_cost"] or 0,
            })

        for pattern, occurrences in pattern_counts.items():
            if len(occurrences) >= 3:
                avg_duration = sum(o["avg_duration"] for o in occurrences) / len(occurrences)
                total_cost = sum(o["total_cost"] for o in occurrences)
                estimated_savings = avg_duration * 0.3 * len(occurrences)  # 30% time savings

                recommendations.append({
                    "type": "macro_opportunity",
                    "priority": "high" if len(occurrences) >= 5 else "medium",
                    "description": f"Create macro for pattern: {pattern}",
                    "details": {
                        "pattern": pattern,
                        "times_used": len(occurrences),
                        "avg_duration": round(avg_duration, 1),
                        "estimated_savings_seconds": round(estimated_savings, 1),
                        "estimated_savings_usd": round(total_cost * 0.3, 2),
                    },
                    "estimated_savings_seconds": round(estimated_savings, 1),
                    "estimated_savings_usd": round(total_cost * 0.3, 2),
                })

        return recommendations

    def _analyze_agent_performance(self) -> List[Dict]:
        """Compare agent efficiency"""
        agent_stats = self.metrics.db.execute("""
            SELECT
                agent_name,
                task_type,
                AVG(duration_seconds) as avg_duration,
                COUNT(*) as task_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM task_executions
            WHERE started_at >= date('now', '-7 days')
            GROUP BY agent_name, task_type
            HAVING task_count >= 3
        """).fetchall()

        # Group by task type
        task_types = defaultdict(list)
        for stat in agent_stats:
            task_types[stat["task_type"]].append({
                "agent": stat["agent_name"],
                "duration": stat["avg_duration"] or 0,
                "success_rate": stat["success_rate"] or 0,
                "task_count": stat["task_count"],
            })

        recommendations = []
        for task_type, agents in task_types.items():
            if len(agents) < 2:
                continue

            # Find best and worst performers
            agents_sorted = sorted(agents, key=lambda a: a["duration"] / (a["success_rate"] / 100 if a["success_rate"] > 0 else 1))
            best = agents_sorted[0]
            worst = agents_sorted[-1]

            improvement = ((worst["duration"] - best["duration"]) / worst["duration"]) * 100

            if improvement > 20:  # 20% improvement potential
                recommendations.append({
                    "type": "agent_optimization",
                    "priority": "medium",
                    "description": f"Use {best['agent']} for {task_type} tasks (30% faster)",
                    "details": {
                        "task_type": task_type,
                        "best_agent": best["agent"],
                        "improvement_percent": round(improvement, 1),
                        "estimated_savings_seconds": round(worst["duration"] - best["duration"], 1),
                    },
                    "estimated_savings_seconds": round(worst["duration"] - best["duration"], 1),
                })

        return recommendations

    def _cost_optimization(self) -> List[Dict]:
        """Identify cost-saving opportunities"""
        recommendations = []

        # Check for expensive task types
        expensive_tasks = self.metrics.db.execute("""
            SELECT task_type,
                   AVG(cost_usd) as avg_cost,
                   COUNT(*) as task_count,
                   SUM(cost_usd) as total_cost
            FROM task_executions
            WHERE started_at >= date('now', '-30 days')
            GROUP BY task_type
            HAVING task_count >= 5
            ORDER BY avg_cost DESC
            LIMIT 5
        """).fetchall()

        for task in expensive_tasks:
            if task["avg_cost"] > 0.10:  # More than $0.10 per task
                potential_savings = task["total_cost"] * 0.2  # 20% savings potential

                recommendations.append({
                    "type": "cost_optimization",
                    "priority": "high" if task["avg_cost"] > 0.50 else "medium",
                    "description": f"Optimize {task['task_type']} tasks (${task['avg_cost']:.2f}/task)",
                    "details": {
                        "task_type": task["task_type"],
                        "avg_cost": round(task["avg_cost"], 2),
                        "task_count": task["task_count"],
                        "potential_savings": round(potential_savings, 2),
                    },
                    "estimated_savings_usd": round(potential_savings, 2),
                })

        return recommendations


class AnalyticsDashboard:
    """Terminal-based analytics dashboard"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.recommendations_engine = RecommendationsEngine(metrics_collector)

    def get_summary(self, time_period: str = "today") -> str:
        """Get text summary of metrics"""
        metrics = self.metrics.get_metrics(time_period)

        task_metrics = metrics.get("tasks", {})
        cost_metrics = metrics.get("cost", {})
        perf_metrics = metrics.get("performance", {})

        summary = f"""
📊 Analytics Summary ({time_period})

Tasks:
  Total: {task_metrics.get('total_tasks', 0)}
  Completed: {task_metrics.get('completed_tasks', 0)}
  Failed: {task_metrics.get('failed_tasks', 0)}
  Success Rate: {task_metrics.get('success_rate', 0)}%
  Avg Duration: {task_metrics.get('avg_duration_seconds', 0):.1f}s

Costs:
  Total: ${cost_metrics.get('total_cost', 0):.2f}
"""

        # Add top cost drivers
        by_agent = cost_metrics.get("by_agent_type", [])
        if by_agent:
            summary += "\n  By Agent Type:\n"
            for agent in by_agent[:3]:
                summary += f"    {agent['agent_tool']}: ${agent['cost']:.2f} ({agent['tasks']} tasks)\n"

        # Add performance insights
        agent_eff = perf_metrics.get("agent_efficiency", [])
        if agent_eff:
            summary += "\n  Top Performing Agents:\n"
            for agent in agent_eff[:3]:
                summary += f"    {agent['agent_name']}: {agent['tasks_per_hour']:.1f} tasks/hr ({agent['success_rate']:.0f}% success)\n"

        return summary

    def get_recommendations(self) -> str:
        """Get optimization recommendations"""
        recommendations = self.recommendations_engine.generate_recommendations()

        if not recommendations:
            return "No recommendations at this time."

        output = "💡 Optimization Recommendations:\n\n"

        for i, rec in enumerate(recommendations[:5], 1):
            output += f"{i}. [{rec['priority'].upper()}] {rec['description']}\n"
            if rec.get("estimated_savings_seconds"):
                output += f"   Estimated savings: {rec['estimated_savings_seconds']:.0f}s/day\n"
            if rec.get("estimated_savings_usd"):
                output += f"   Cost savings: ${rec['estimated_savings_usd']:.2f}/day\n"
            output += "\n"

        return output
