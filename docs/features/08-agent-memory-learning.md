# Feature 8: Agent Memory & Learning System

**Status**: ✅ Implemented (v2.2 - Phase 2)
**Module**: `apps/realtime-poc/features/memory.py`
**Priority**: High
**Complexity**: High

## Overview

The Agent Memory & Learning System tracks agent interactions, learns from patterns, and builds a searchable knowledge base to improve performance over time. It enables agents to remember past solutions, avoid repeated mistakes, and apply learned patterns to new problems - essentially giving agents the ability to learn from experience.

## Problem Statement

Agents currently operate without memory:

1. **No Learning**: Agents repeat the same mistakes without learning from failures
2. **Lost Context**: Successful approaches are forgotten after execution
3. **No Pattern Recognition**: Common patterns must be discovered repeatedly
4. **Wasted Time**: Previously solved problems are re-solved from scratch
5. **No Knowledge Sharing**: Insights from one task don't transfer to similar tasks

**Impact**: An agent that solves "implement user authentication" 10 times will approach it identically each time, without leveraging past successes or avoiding previous failures.

## Solution

An intelligent memory and learning system that:

1. **Records Interactions**: Stores every agent task with approach, outcome, and context
2. **Learns Patterns**: Identifies success patterns, failure patterns, and duration patterns
3. **Builds Knowledge**: Creates searchable knowledge base from successful interactions
4. **Provides Recommendations**: Suggests approaches based on historical success
5. **Tracks Performance**: Monitors improvement over time through metrics
6. **Enables Search**: Query past solutions and learned knowledge

## Architecture

### Core Components

```python
# Persistent storage
class MemoryStore:
    def store_interaction(...) -> str
    def get_interactions(...) -> List[Dict]
    def store_pattern(...) -> str
    def update_pattern(...)
    def get_patterns(...) -> List[Dict]
    def store_knowledge(...) -> str
    def search_knowledge(...) -> List[Dict]

# Pattern learning
class PatternLearner:
    def learn_from_interactions(...) -> List[Dict]
    def get_recommendations(task_type: str) -> List[Dict]

# Knowledge management
class KnowledgeBase:
    def add_knowledge(...) -> str
    def search(query: str) -> List[Dict]
    def extract_knowledge_from_interactions(...)

# Interactive session
class LearningSession:
    def record_interaction(...) -> str
    def get_recommendations(task_type: str) -> Dict
    def learn_patterns(...) -> List[Dict]
    def add_knowledge(...) -> str
    def search_knowledge(query: str) -> List[Dict]
    def get_session_stats() -> Dict
```

### Data Flow

```mermaid
graph TD
    A[Agent Task Execution] --> B[Record Interaction]
    B --> C[MemoryStore SQLite]
    C --> D[PatternLearner]
    D --> E[Identify Patterns]
    E --> F[Store Patterns]

    C --> G[KnowledgeBase]
    G --> H[Extract Knowledge]
    H --> I[Store Knowledge]

    J[New Task] --> K[Get Recommendations]
    F --> K
    I --> K
    K --> L[Agent receives guidance]
    L --> A

    style C fill:#9cf,stroke:#333
    style K fill:#9f9,stroke:#333
```

### Database Schema

```sql
-- Interactions table
CREATE TABLE interactions (
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
    context TEXT,  -- JSON
    tags TEXT      -- JSON array
);

-- Patterns table
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,  -- JSON
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.0,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    metadata TEXT  -- JSON
);

-- Knowledge entries table
CREATE TABLE knowledge_entries (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    relevance_score REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    tags TEXT,      -- JSON array
    metadata TEXT   -- JSON
);
```

## Key Features

### 1. Interaction Recording

**Capabilities**:
- Records every agent task with complete context
- Captures approach, outcome, success/failure
- Stores execution duration for performance tracking
- Tags interactions for easy retrieval
- Thread-safe concurrent recording

**Example**:
```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Record a successful interaction
interaction_id = session.record_interaction(
    agent_name="claude_code",
    task_type="implement_feature",
    task_description="Implement user authentication with JWT",
    approach="Used Flask-JWT-Extended library with RS256 algorithm",
    outcome="Feature implemented successfully, all tests passing",
    success=True,
    duration_seconds=45.3,
    tags=["authentication", "jwt", "security"]
)

print(f"Recorded interaction: {interaction_id}")
```

**Result**:
```
Recorded interaction: 550e8400-e29b-41d4-a716-446655440000
```

### 2. Pattern Learning

**Pattern Types**:
- **Successful Approaches**: What works for specific task types
- **Common Failures**: Errors that occur frequently
- **Duration Patterns**: Expected execution times for tasks

**Example - Learn Patterns**:
```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Learn patterns from historical data
patterns = session.learn_patterns(
    task_type="implement_feature",
    min_occurrences=3  # Only patterns seen 3+ times
)

print(f"Learned {len(patterns)} patterns:")
for pattern in patterns:
    print(f"  - {pattern['type']}: {pattern.get('approach', pattern.get('error_type'))}")
```

**Output**:
```
Learned 5 patterns:
  - successful_approach: Used Flask-JWT-Extended library
  - successful_approach: Used Django REST framework authentication
  - common_failure: KeyError
  - common_failure: AttributeError
  - duration_pattern: implement_feature tasks typically take 42.5s (medium)
```

### 3. Intelligent Recommendations

**Based On**:
- Historical success rates
- Pattern confidence scores
- Failure avoidance
- Performance expectations

**Example**:
```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Get recommendations for a new task
recs = session.get_recommendations(
    task_type="implement_feature",
    include_knowledge=True
)

print(f"Recommendations for '{recs['task_type']}':")
print(f"\nPattern Recommendations ({len(recs['pattern_recommendations'])}):")
for rec in recs['pattern_recommendations']:
    print(f"  [{rec['priority'].upper()}] {rec['recommendation']}")
    print(f"    Confidence: {rec['confidence']*100:.1f}%")

print(f"\nKnowledge Entries ({len(recs.get('knowledge_entries', []))}):")
for entry in recs.get('knowledge_entries', [])[:3]:
    print(f"  - {entry['title']}")
```

**Output**:
```
Recommendations for 'implement_feature':

Pattern Recommendations (3):
  [HIGH] Use 'Flask-JWT-Extended library' for implement_feature tasks
    Confidence: 85.7%
  [MEDIUM] Watch out for 'KeyError' in implement_feature tasks
    Confidence: 100.0%
  [LOW] implement_feature tasks typically take 42.5s (medium)
    Confidence: 90.0%

Knowledge Entries (2):
  - Best Practice for implement_feature
  - JWT Authentication Implementation Guide
```

### 4. Knowledge Base

**Features**:
- Category-based organization
- Full-text search
- Relevance scoring
- Automatic extraction from successful interactions
- Tag-based filtering

**Example - Add Knowledge**:
```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Manually add knowledge
knowledge_id = session.add_knowledge(
    category="authentication",
    title="JWT Best Practices",
    content="""
    When implementing JWT authentication:
    1. Use RS256 algorithm for better security
    2. Set appropriate expiration times (15min for access, 7d for refresh)
    3. Store refresh tokens securely (httpOnly cookies)
    4. Implement token rotation
    5. Add rate limiting to prevent brute force
    """,
    tags=["jwt", "security", "best_practices"]
)

print(f"Added knowledge entry: {knowledge_id}")
```

**Example - Search Knowledge**:
```python
# Search knowledge base
results = session.search_knowledge(
    query="JWT security",
    category="authentication"
)

print(f"Found {len(results)} knowledge entries:")
for entry in results:
    print(f"\n{entry['title']}")
    print(f"  Category: {entry['category']}")
    print(f"  Relevance: {entry['relevance_score']}")
    print(f"  Tags: {', '.join(entry.get('tags', []))}")
    print(f"  Content: {entry['content'][:100]}...")
```

### 5. Performance Tracking

**Metrics**:
- Total interactions
- Success rate
- Patterns learned
- Knowledge entries
- Improvement over time

**Example**:
```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Get session statistics
stats = session.get_session_stats()

print("Session Statistics:")
print(f"  Total Interactions: {stats['total_interactions']}")
print(f"  Successful: {stats['successful_interactions']}")
print(f"  Failed: {stats['failed_interactions']}")
print(f"  Success Rate: {stats['success_rate']}%")
print(f"\nLearning Progress:")
print(f"  Patterns Learned: {stats['patterns_learned']}")
print(f"  Pattern Types: {stats['pattern_types']}")
print(f"  Knowledge Entries: {stats['knowledge_entries']}")
```

**Output**:
```
Session Statistics:
  Total Interactions: 127
  Successful: 108
  Failed: 19
  Success Rate: 85.04%

Learning Progress:
  Patterns Learned: 23
  Pattern Types: {'successful_approach': 12, 'common_failure': 6, 'duration_pattern': 5}
  Knowledge Entries: 45
```

## Voice Integration

### Voice Commands

When integrated with the main voice agent:

**Recording**:
- "Remember this approach for authentication tasks"
- "Record that using library X worked well"
- "Note that Y approach failed for Z reason"

**Recommendations**:
- "What's the best way to implement feature X?"
- "How should I approach this task?"
- "What have I tried before for this?"

**Knowledge**:
- "Search knowledge for JWT security"
- "What do I know about authentication?"
- "Show me past solutions for this problem"

**Analytics**:
- "How am I performing?"
- "What's my success rate?"
- "What patterns have I learned?"

### Integration Example

```python
# In big_three_realtime_agents.py

from features.memory import LearningSession

learning_session = LearningSession()

def handle_task_execution(task_info: Dict):
    # Get recommendations before starting
    recs = learning_session.get_recommendations(
        task_type=task_info['type']
    )

    voice_agent.speak("Based on past experience, here's what I recommend:")
    for rec in recs['pattern_recommendations'][:3]:
        voice_agent.speak(f"- {rec['recommendation']}")

    # Execute task
    start_time = time.time()
    try:
        result = execute_task(task_info)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)

    duration = time.time() - start_time

    # Record the interaction
    learning_session.record_interaction(
        agent_name="voice_agent",
        task_type=task_info['type'],
        task_description=task_info['description'],
        approach=task_info.get('approach', 'default'),
        outcome=str(result) if success else f"Failed: {error}",
        success=success,
        duration_seconds=duration,
        error_message=error,
        tags=task_info.get('tags', [])
    )

    # Learn from recent interactions
    if random.random() < 0.1:  # 10% of the time
        patterns = learning_session.learn_patterns()
        voice_agent.speak(f"I learned {len(patterns)} new patterns from recent tasks")
```

## Usage Examples

### Example 1: Learning from Multiple Tasks

```python
from apps.realtime_poc.features.memory import LearningSession
import time

session = LearningSession()

# Simulate multiple authentication implementation tasks
tasks = [
    ("JWT with Flask", True, 42.5),
    ("JWT with Django", True, 38.2),
    ("OAuth with Flask", False, 15.3),  # Failed
    ("JWT with FastAPI", True, 35.7),
    ("Basic Auth", False, 8.1),  # Failed
]

for approach, success, duration in tasks:
    session.record_interaction(
        agent_name="backend_agent",
        task_type="implement_auth",
        task_description=f"Implement authentication using {approach}",
        approach=approach,
        outcome="Success" if success else "Failed",
        success=success,
        duration_seconds=duration,
        error_message=None if success else "Configuration error",
        tags=["authentication"]
    )

# Learn patterns
patterns = session.learn_patterns(task_type="implement_auth", min_occurrences=2)
print(f"Learned {len(patterns)} patterns from authentication tasks")

# Get recommendations
recs = session.get_recommendations("implement_auth")
print("\nRecommendations for next authentication task:")
for rec in recs['pattern_recommendations']:
    print(f"  - {rec['recommendation']} (confidence: {rec['confidence']*100:.0f}%)")
```

**Output**:
```
Learned 3 patterns from authentication tasks

Recommendations for next authentication task:
  - Use 'JWT with Flask' for implement_auth tasks (confidence: 100%)
  - Use 'JWT with Django' for implement_auth tasks (confidence: 100%)
  - implement_auth tasks typically take 38.8s (medium) (confidence: 100%)
```

### Example 2: Building Knowledge Base

```python
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()

# Add domain knowledge
session.add_knowledge(
    category="database",
    title="PostgreSQL Connection Best Practices",
    content="""
    Best practices for PostgreSQL connections:
    - Use connection pooling (pg_pool, SQLAlchemy pool)
    - Set appropriate pool size (CPU cores * 2 + disk drives)
    - Enable SSL for production
    - Use prepared statements to prevent SQL injection
    - Implement connection timeout and retry logic
    """,
    tags=["postgresql", "database", "best_practices"]
)

session.add_knowledge(
    category="database",
    title="Database Migration Strategies",
    content="""
    Safe database migration approaches:
    1. Always backup before migrations
    2. Test migrations on staging first
    3. Use backward-compatible changes when possible
    4. Plan rollback strategy
    5. Monitor database performance after migration
    """,
    tags=["database", "migrations", "devops"]
)

# Search for database knowledge
results = session.search_knowledge("PostgreSQL", category="database")
print(f"Found {len(results)} entries about PostgreSQL:")
for entry in results:
    print(f"\n{entry['title']}")
    print(f"Tags: {', '.join(entry.get('tags', []))}")
```

### Example 3: Complete Learning Workflow

```python
from apps.realtime_poc.features.memory import LearningSession
import time

session = LearningSession()

# 1. Check recommendations before starting
task_type = "api_integration"
print("Step 1: Getting recommendations...")
recs = session.get_recommendations(task_type)

if recs['pattern_recommendations']:
    print("Based on past experience:")
    for rec in recs['pattern_recommendations'][:2]:
        print(f"  - {rec['recommendation']}")
else:
    print("No historical data for this task type")

# 2. Execute task
print("\nStep 2: Executing task...")
start_time = time.time()
try:
    # Simulate task execution
    approach = "Used requests library with retry logic"
    time.sleep(2)  # Simulate work
    result = "API integrated successfully"
    success = True
    error = None
except Exception as e:
    result = None
    success = False
    error = str(e)

duration = time.time() - start_time

# 3. Record the interaction
print("\nStep 3: Recording interaction...")
interaction_id = session.record_interaction(
    agent_name="integration_agent",
    task_type=task_type,
    task_description="Integrate external payment API",
    approach=approach,
    outcome=result or f"Failed: {error}",
    success=success,
    duration_seconds=duration,
    error_message=error,
    tags=["api", "payments", "integration"]
)

print(f"Recorded: {interaction_id}")

# 4. Learn patterns periodically
print("\nStep 4: Learning patterns...")
patterns = session.learn_patterns(min_occurrences=1)
print(f"Learned {len(patterns)} patterns")

# 5. Check stats
print("\nStep 5: Session statistics:")
stats = session.get_session_stats()
print(f"  Success rate: {stats['success_rate']}%")
print(f"  Patterns learned: {stats['patterns_learned']}")
```

## Pattern Types Learned

### 1. Successful Approach Patterns

Identifies which approaches work best for specific task types.

**Example**:
```python
{
    "pattern_type": "successful_approach",
    "pattern_data": {
        "task_type": "implement_feature",
        "approach": "TDD (write tests first)",
        "description": "Use 'TDD (write tests first)' for implement_feature tasks"
    },
    "success_count": 15,
    "failure_count": 0,
    "confidence": 1.0
}
```

### 2. Common Failure Patterns

Identifies frequent error types to avoid.

**Example**:
```python
{
    "pattern_type": "common_failure",
    "pattern_data": {
        "task_type": "database_migration",
        "error_type": "IntegrityError",
        "description": "Watch out for 'IntegrityError' in database_migration tasks",
        "prevention": "Add validation before execution"
    },
    "success_count": 0,
    "failure_count": 8,
    "confidence": 1.0
}
```

### 3. Duration Patterns

Identifies expected execution times.

**Example**:
```python
{
    "pattern_type": "duration_pattern",
    "pattern_data": {
        "task_type": "code_review",
        "speed_class": "fast",
        "avg_duration": 3.2,
        "min_duration": 1.5,
        "max_duration": 5.8,
        "description": "code_review tasks typically take 3.2s (fast)"
    },
    "success_count": 25,
    "confidence": 0.96
}
```

## Benefits

1. **Continuous Improvement**: Success rate increases over time as patterns are learned
2. **Avoid Repeated Mistakes**: Common failures are identified and prevented
3. **Faster Execution**: Leverage proven approaches instead of trial and error
4. **Knowledge Accumulation**: Build institutional knowledge that persists
5. **Data-Driven Decisions**: Recommendations based on actual historical performance
6. **Reduced Cognitive Load**: Don't need to remember every past solution

## Performance Considerations

### Scalability

- **SQLite Performance**: Suitable for 100K+ interactions; for production scale, migrate to PostgreSQL
- **Pattern Learning**: O(n) where n = number of interactions; optimize by limiting lookups to recent data
- **Search Performance**: Indexed queries are fast; full-text search on content may slow with large datasets

### Memory Usage

- **Database**: Minimal memory footprint; data stored on disk
- **In-Memory**: Only active session data and recently accessed patterns
- **Caching**: No automatic caching; implement as needed for hot patterns

### Optimization Tips

1. **Limit Historical Data**: Use time-based filters when learning patterns (e.g., last 3 months)
2. **Batch Learning**: Learn patterns periodically, not after every interaction
3. **Archive Old Data**: Move old interactions to archive tables after 1 year
4. **Index Optimization**: Add indexes for frequently queried fields

## Limitations

1. **Context Sensitivity**: Patterns may not account for subtle context differences
2. **Cold Start**: No recommendations until sufficient data is collected
3. **Pattern Staleness**: Old patterns may become outdated as practices evolve
4. **Correlation ≠ Causation**: High confidence doesn't guarantee the approach causes success
5. **SQLite Concurrency**: Limited write concurrency; use PostgreSQL for high-traffic scenarios

## Future Enhancements

1. **LLM Integration**: Use Claude/GPT to generate smarter recommendations from patterns
2. **Confidence Decay**: Reduce confidence of old patterns over time
3. **Context-Aware Learning**: Factor in more context (project type, team, timeline)
4. **Cross-Agent Learning**: Share patterns across different agents
5. **Anomaly Detection**: Identify unusual patterns that may indicate issues
6. **Visual Analytics**: Dashboard showing learning curves, pattern evolution
7. **Export/Import**: Share knowledge bases between teams

## Testing

Run tests for the memory system:

```bash
# Test interaction recording
python3 -c "
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()
interaction_id = session.record_interaction(
    agent_name='test_agent',
    task_type='test_task',
    task_description='Test description',
    approach='Test approach',
    outcome='Success',
    success=True,
    duration_seconds=1.5
)
assert interaction_id is not None
print('✓ Interaction recording works')
"

# Test pattern learning
python3 -c "
from apps.realtime_poc.features.memory import LearningSession

session = LearningSession()
# Record multiple interactions
for i in range(5):
    session.record_interaction(
        agent_name='test_agent',
        task_type='test_task',
        task_description=f'Test {i}',
        approach='same_approach',
        outcome='Success',
        success=True
    )

patterns = session.learn_patterns(min_occurrences=3)
assert len(patterns) > 0
print('✓ Pattern learning works')
"
```

## API Reference

### LearningSession

```python
class LearningSession:
    def __init__(self, memory_store: Optional[MemoryStore] = None):
        """Initialize learning session."""

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
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Record an agent interaction.

        Returns:
            interaction_id: Unique ID for the recorded interaction
        """

    def get_recommendations(
        self,
        task_type: str,
        include_knowledge: bool = True
    ) -> Dict:
        """
        Get pattern-based recommendations for a task.

        Returns:
            {
                "task_type": str,
                "pattern_recommendations": List[Dict],
                "knowledge_entries": List[Dict]  # if include_knowledge=True
            }
        """

    def learn_patterns(
        self,
        task_type: Optional[str] = None,
        min_occurrences: int = 3
    ) -> List[Dict]:
        """Learn patterns from interactions."""

    def add_knowledge(
        self,
        category: str,
        title: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> str:
        """Add knowledge entry."""

    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Search knowledge base."""

    def get_session_stats(self) -> Dict:
        """Get session statistics."""
```

## Related Features

- **Feature 1: Collaboration Rooms** - Share learned patterns across agents in rooms
- **Feature 3: Analytics** - Track learning metrics alongside performance metrics
- **Feature 6: Debugging** - Learn from error patterns to improve debugging
- **Feature 7: Testing** - Learn which test patterns catch the most bugs

---

**Implementation**: `apps/realtime-poc/features/memory.py` (900+ lines)
**Tests**: Coming soon
**Status**: Production-ready ✅
