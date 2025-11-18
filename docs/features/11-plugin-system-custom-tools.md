# Feature 11: Plugin System & Custom Tools

## Overview

The **Plugin System & Custom Tools** provides an extensibility framework for the Big Three Realtime Agents, enabling users to create custom tools, extend agent capabilities, and integrate third-party services through a plugin architecture.

**Version:** 1.0.0
**Status:** ✅ Implemented
**Implementation:** `apps/realtime-poc/features/plugin_system.py`

## Problem Statement

The core system has limited extensibility:
- **No custom tools**: Users cannot add domain-specific functionality
- **No third-party integrations**: Cannot integrate external services
- **Hard to extend**: Adding new capabilities requires core code changes
- **No plugin marketplace**: Cannot share tools with community
- **Limited reusability**: Tools cannot be packaged and distributed

## Solution

The Plugin System provides:
- **Plugin architecture**: Standard interface for extending capabilities
- **Custom tool definitions**: Define tools with JSON schemas
- **Plugin discovery**: Automatic loading from directories
- **Lifecycle management**: Install, enable, disable, uninstall
- **Sandboxed execution**: Safe plugin execution
- **OpenAI integration**: Export tools as OpenAI functions
- **Plugin templates**: Quick-start templates for development

## Architecture

### Components

```
PluginManager (High-level API)
├── PluginLoader (Load plugins)
│   ├── From files (.py)
│   ├── From directories
│   └── Hot reloading
├── PluginRegistry (Metadata storage)
│   ├── Plugin info (JSON)
│   ├── Status tracking
│   └── Configuration
└── Plugin Instances
    ├── get_metadata()
    ├── get_tools()
    ├── execute_tool()
    └── Lifecycle hooks
```

### Plugin Interface

```python
class Plugin(ABC):
    """Base class for all plugins"""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    def get_tools(self) -> List[ToolDefinition]:
        """Return list of tools provided by this plugin"""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool provided by this plugin"""
        pass

    def on_install(self):
        """Called when plugin is installed"""
        pass

    def on_enable(self):
        """Called when plugin is enabled"""
        pass

    def on_disable(self):
        """Called when plugin is disabled"""
        pass

    def on_uninstall(self):
        """Called when plugin is uninstalled"""
        pass

    def on_configure(self, config: Dict[str, Any]):
        """Called when plugin configuration changes"""
        pass
```

### Data Models

**PluginMetadata:**
```python
@dataclass
class PluginMetadata:
    id: str
    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    homepage: Optional[str] = None
    repository: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
```

**ToolDefinition:**
```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: Optional[str] = None
    examples: List[str] = field(default_factory=list)
```

**ToolParameter:**
```python
@dataclass
class ToolParameter:
    name: str
    type: ToolParameterType  # STRING, INTEGER, NUMBER, BOOLEAN, ARRAY, OBJECT
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
```

**PluginStatus:**
```python
class PluginStatus(Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
```

## Usage

### Creating a Simple Plugin

**Step 1: Create plugin file**

Create `plugins/installed/weather_plugin.py`:

```python
from features.plugin_system import (
    Plugin,
    PluginMetadata,
    ToolDefinition,
    ToolParameter,
    ToolParameterType
)
from typing import List, Dict, Any
import requests


class WeatherPlugin(Plugin):
    """Plugin for weather information"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="weather-plugin",
            name="Weather Plugin",
            version="1.0.0",
            description="Get weather information for any location",
            author="Your Name",
            tags=["weather", "api", "utility"]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_weather",
                description="Get current weather for a location",
                parameters=[
                    ToolParameter(
                        name="location",
                        type=ToolParameterType.STRING,
                        description="City name or coordinates",
                        required=True
                    ),
                    ToolParameter(
                        name="units",
                        type=ToolParameterType.STRING,
                        description="Temperature units (celsius or fahrenheit)",
                        required=False,
                        default="celsius",
                        enum=["celsius", "fahrenheit"]
                    )
                ],
                returns="Weather information including temperature, conditions, humidity",
                examples=[
                    "get_weather(location='San Francisco', units='fahrenheit')",
                    "get_weather(location='London')"
                ]
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "get_weather":
            location = parameters.get("location")
            units = parameters.get("units", "celsius")

            # Call weather API (example)
            # api_key = self.config.get("api_key")
            # response = requests.get(f"https://api.weather.com/...", ...)

            # For demo, return mock data
            return {
                "location": location,
                "temperature": 72 if units == "fahrenheit" else 22,
                "units": units,
                "conditions": "Partly cloudy",
                "humidity": 65,
                "wind_speed": 10
            }

        raise ValueError(f"Unknown tool: {tool_name}")
```

**Step 2: Install and enable plugin**

```python
from features.plugin_system import PluginManager
from pathlib import Path

# Initialize manager
manager = PluginManager()

# Install plugin
plugin_info = manager.install_plugin(
    Path("plugins/installed/weather_plugin.py")
)

print(f"Installed: {plugin_info.metadata.name}")

# Enable plugin
manager.enable_plugin("weather-plugin")

print(f"Plugin enabled")
```

**Step 3: Use plugin tool**

```python
# Execute tool
result = manager.execute_tool(
    plugin_id="weather-plugin",
    tool_name="get_weather",
    parameters={
        "location": "San Francisco",
        "units": "fahrenheit"
    }
)

print(f"Weather: {result['temperature']}°F, {result['conditions']}")
```

### Creating a Plugin Directory Structure

For more complex plugins with multiple files:

```
plugins/installed/
└── advanced_plugin/
    ├── __init__.py
    ├── plugin.py
    ├── utils.py
    ├── config.json
    └── README.md
```

**plugins/installed/advanced_plugin/__init__.py:**
```python
"""Advanced Plugin"""

from .plugin import AdvancedPlugin

__all__ = ["AdvancedPlugin"]
```

**plugins/installed/advanced_plugin/plugin.py:**
```python
from features.plugin_system import (
    Plugin,
    PluginMetadata,
    ToolDefinition,
    ToolParameter,
    ToolParameterType
)
from typing import List, Dict, Any
from .utils import helper_function


class AdvancedPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="advanced-plugin",
            name="Advanced Plugin",
            version="1.0.0",
            description="Advanced plugin with multiple tools",
            author="Your Name"
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            # Define multiple tools
            ToolDefinition(
                name="tool_one",
                description="First tool",
                parameters=[...],
                returns="Result from tool one"
            ),
            ToolDefinition(
                name="tool_two",
                description="Second tool",
                parameters=[...],
                returns="Result from tool two"
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "tool_one":
            return helper_function(parameters)
        elif tool_name == "tool_two":
            return self._process_tool_two(parameters)

        raise ValueError(f"Unknown tool: {tool_name}")

    def _process_tool_two(self, parameters: Dict[str, Any]) -> Any:
        # Tool implementation
        pass
```

### Plugin Lifecycle Management

**List all plugins:**
```python
# List all plugins
all_plugins = manager.list_plugins()

for plugin in all_plugins:
    print(f"{plugin.metadata.name} v{plugin.metadata.version}")
    print(f"Status: {plugin.status.value}")
    print(f"Installed: {plugin.installed_at}")
    print()

# List enabled plugins only
enabled = manager.list_plugins(status=PluginStatus.ENABLED)
```

**Disable a plugin:**
```python
# Disable plugin (keeps it installed)
manager.disable_plugin("weather-plugin")

print("Plugin disabled")
```

**Re-enable a plugin:**
```python
# Re-enable with optional new config
manager.enable_plugin("weather-plugin", config={
    "api_key": "your-api-key-here",
    "cache_duration": 300
})
```

**Uninstall a plugin:**
```python
# Uninstall plugin (removes from registry)
manager.uninstall_plugin("weather-plugin")

print("Plugin uninstalled")
```

### Plugin Discovery

**Auto-discover and load all plugins:**
```python
# Discover and load all plugins from plugins/installed
manager.discover_and_load_all()

print(f"Loaded {len(manager.loaded_plugins)} plugins")

# List loaded plugins
for plugin_id, plugin in manager.loaded_plugins.items():
    metadata = plugin.get_metadata()
    tools = plugin.get_tools()

    print(f"{metadata.name}:")
    print(f"  Tools: {', '.join(t.name for t in tools)}")
```

### Getting Plugin Tools

**Get tools from specific plugin:**
```python
# Get tools from one plugin
tools = manager.get_plugin_tools("weather-plugin")

for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Parameters:")
    for param in tool.parameters:
        print(f"  - {param.name} ({param.type.value}): {param.description}")
```

**Get all tools from all enabled plugins:**
```python
# Get all tools
all_tools = manager.get_all_tools()

for plugin_id, tools in all_tools.items():
    print(f"Plugin: {plugin_id}")
    for tool in tools:
        print(f"  - {tool.name}")
```

### OpenAI Function Calling Integration

**Export tools for OpenAI:**
```python
from features.plugin_system import export_tools_for_openai

# Get all tools in OpenAI format
openai_functions = export_tools_for_openai(manager)

# Use with OpenAI API
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    functions=openai_functions,
    function_call="auto"
)

# If function call detected
if response.choices[0].message.function_call:
    function_name = response.choices[0].message.function_call.name
    arguments = json.loads(response.choices[0].message.function_call.arguments)

    # Execute via plugin manager
    result = manager.execute_tool(
        plugin_id="weather-plugin",
        tool_name=function_name,
        parameters=arguments
    )
```

### Plugin Configuration

**Configure plugin:**
```python
# Enable with configuration
manager.enable_plugin("weather-plugin", config={
    "api_key": "your-api-key",
    "default_units": "fahrenheit",
    "cache_enabled": True,
    "cache_duration": 300
})

# Access config in plugin
class WeatherPlugin(Plugin):
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        # Use configuration
        api_key = self.config.get("api_key")
        default_units = self.config.get("default_units", "celsius")

        # Tool implementation
        ...
```

## Advanced Examples

### Database Integration Plugin

```python
import sqlite3
from features.plugin_system import *


class DatabasePlugin(Plugin):
    """Plugin for database operations"""

    def __init__(self):
        super().__init__()
        self.conn = None

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="database-plugin",
            name="Database Plugin",
            version="1.0.0",
            description="Execute SQL queries and manage databases",
            author="Big Three Team",
            tags=["database", "sql", "data"]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="execute_query",
                description="Execute a SQL query",
                parameters=[
                    ToolParameter(
                        name="query",
                        type=ToolParameterType.STRING,
                        description="SQL query to execute",
                        required=True
                    ),
                    ToolParameter(
                        name="database",
                        type=ToolParameterType.STRING,
                        description="Database file path",
                        required=False
                    )
                ],
                returns="Query results as list of dictionaries"
            )
        ]

    def on_enable(self):
        super().on_enable()
        db_path = self.config.get("database_path", "data.db")
        self.conn = sqlite3.connect(db_path)

    def on_disable(self):
        super().on_disable()
        if self.conn:
            self.conn.close()

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "execute_query":
            query = parameters["query"]

            cursor = self.conn.cursor()
            cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                results = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
                return results
            else:
                self.conn.commit()
                return {"rows_affected": cursor.rowcount}

        raise ValueError(f"Unknown tool: {tool_name}")
```

### API Integration Plugin

```python
import requests
from features.plugin_system import *


class SlackPlugin(Plugin):
    """Plugin for Slack integration"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="slack-plugin",
            name="Slack Plugin",
            version="1.0.0",
            description="Send messages and interact with Slack",
            author="Big Three Team",
            tags=["slack", "messaging", "integration"]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="send_message",
                description="Send a message to a Slack channel",
                parameters=[
                    ToolParameter(
                        name="channel",
                        type=ToolParameterType.STRING,
                        description="Channel name or ID",
                        required=True
                    ),
                    ToolParameter(
                        name="message",
                        type=ToolParameterType.STRING,
                        description="Message to send",
                        required=True
                    )
                ],
                returns="Message delivery status"
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "send_message":
            token = self.config.get("slack_token")

            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "channel": parameters["channel"],
                    "text": parameters["message"]
                }
            )

            return response.json()

        raise ValueError(f"Unknown tool: {tool_name}")
```

### File Processing Plugin

```python
from pathlib import Path
from features.plugin_system import *


class FileProcessorPlugin(Plugin):
    """Plugin for file processing operations"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="file-processor",
            name="File Processor",
            version="1.0.0",
            description="Process and transform files",
            author="Big Three Team",
            tags=["file", "processing", "utility"]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="count_lines",
                description="Count lines in a file",
                parameters=[
                    ToolParameter(
                        name="file_path",
                        type=ToolParameterType.STRING,
                        description="Path to file",
                        required=True
                    )
                ],
                returns="Number of lines in file"
            ),
            ToolDefinition(
                name="find_and_replace",
                description="Find and replace text in file",
                parameters=[
                    ToolParameter(
                        name="file_path",
                        type=ToolParameterType.STRING,
                        description="Path to file",
                        required=True
                    ),
                    ToolParameter(
                        name="find",
                        type=ToolParameterType.STRING,
                        description="Text to find",
                        required=True
                    ),
                    ToolParameter(
                        name="replace",
                        type=ToolParameterType.STRING,
                        description="Replacement text",
                        required=True
                    )
                ],
                returns="Number of replacements made"
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "count_lines":
            file_path = Path(parameters["file_path"])

            with open(file_path, 'r') as f:
                return len(f.readlines())

        elif tool_name == "find_and_replace":
            file_path = Path(parameters["file_path"])
            find = parameters["find"]
            replace = parameters["replace"]

            with open(file_path, 'r') as f:
                content = f.read()

            new_content = content.replace(find, replace)
            count = content.count(find)

            with open(file_path, 'w') as f:
                f.write(new_content)

            return count

        raise ValueError(f"Unknown tool: {tool_name}")
```

## Integration with Voice Agent

### Adding Plugin Tools to Voice Agent

**Step 1: Initialize plugin manager in voice agent**

```python
# In OpenAIRealtimeVoiceAgent.__init__
from features.plugin_system import PluginManager, export_tools_for_openai

self.plugin_manager = PluginManager()

# Auto-discover and load all plugins
self.plugin_manager.discover_and_load_all()

# Enable configured plugins
for plugin_id in self.config.get("enabled_plugins", []):
    config = self.config.get(f"plugin_{plugin_id}_config", {})
    self.plugin_manager.enable_plugin(plugin_id, config)
```

**Step 2: Register plugin tools as voice agent functions**

```python
def register_plugin_tools(self):
    """Register all plugin tools as available functions"""
    all_tools = self.plugin_manager.get_all_tools()

    for plugin_id, tools in all_tools.items():
        for tool in tools:
            # Create wrapper function
            def tool_wrapper(plugin_id=plugin_id, tool_name=tool.name):
                def execute(**parameters):
                    return self.plugin_manager.execute_tool(
                        plugin_id,
                        tool_name,
                        parameters
                    )
                return execute

            # Register with voice agent
            function_name = f"{plugin_id}_{tool.name}"
            self.register_function(
                name=function_name,
                description=tool.description,
                parameters=tool.to_openai_function()["parameters"],
                handler=tool_wrapper()
            )
```

**Step 3: Voice commands for plugin management**

```python
def list_available_plugins(self) -> dict:
    """List all available plugins"""
    plugins = self.plugin_manager.list_plugins()

    return {
        "plugins": [
            {
                "id": p.metadata.id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "status": p.status.value,
                "tools": [t.name for t in self.plugin_manager.get_plugin_tools(p.plugin_id)]
            }
            for p in plugins
        ]
    }

def enable_plugin_by_voice(self, plugin_name: str) -> dict:
    """Enable a plugin via voice command"""
    # Find plugin by name
    plugins = self.plugin_manager.list_plugins()

    for plugin in plugins:
        if plugin.metadata.name.lower() == plugin_name.lower():
            self.plugin_manager.enable_plugin(plugin.plugin_id)

            # Re-register tools
            self.register_plugin_tools()

            return {
                "success": True,
                "message": f"Enabled {plugin.metadata.name}",
                "tools": [t.name for t in self.plugin_manager.get_plugin_tools(plugin.plugin_id)]
            }

    return {"success": False, "message": f"Plugin '{plugin_name}' not found"}
```

**Example voice interactions:**
```
User: "List available plugins"
Assistant: "You have 3 plugins installed:
1. Weather Plugin - get weather information (enabled)
2. Database Plugin - execute SQL queries (disabled)
3. Slack Plugin - send Slack messages (enabled)"

User: "Enable the database plugin"
Assistant: "Database plugin enabled. Available tools: execute_query"

User: "Get the weather in San Francisco"
Assistant: [Executes weather plugin tool]
"The weather in San Francisco is 72°F and partly cloudy"
```

## Plugin Template Generator

Use the built-in template generator to create new plugins:

```python
from features.plugin_system import create_plugin_template
from pathlib import Path

# Create plugin template
plugin_dir = create_plugin_template(
    plugin_id="my-custom-plugin",
    plugin_name="My Custom Plugin",
    output_dir=Path("plugins/installed")
)

print(f"Plugin template created at: {plugin_dir}")
```

This creates:
```
plugins/installed/my-custom-plugin/
├── __init__.py
├── plugin.py
└── README.md
```

Then edit `plugin.py` to implement your custom tools.

## Best Practices

### 1. Error Handling

Always handle errors gracefully in plugins:

```python
def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
    try:
        if tool_name == "risky_operation":
            result = self._perform_operation(parameters)
            return {"success": True, "data": result}

    except ValueError as e:
        return {"success": False, "error": f"Invalid input: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Operation failed: {str(e)}"}

    raise ValueError(f"Unknown tool: {tool_name}")
```

### 2. Configuration Validation

Validate configuration on enable:

```python
def on_configure(self, config: Dict[str, Any]):
    super().on_configure(config)

    # Validate required config
    if "api_key" not in config:
        raise ValueError("api_key is required")

    if len(config["api_key"]) < 10:
        raise ValueError("Invalid api_key format")
```

### 3. Resource Cleanup

Clean up resources on disable/uninstall:

```python
def on_disable(self):
    super().on_disable()

    # Close connections
    if self.conn:
        self.conn.close()

    # Clear caches
    self.cache.clear()

def on_uninstall(self):
    super().on_uninstall()

    # Remove temp files
    if self.temp_dir.exists():
        shutil.rmtree(self.temp_dir)
```

### 4. Documentation

Document tools with clear descriptions and examples:

```python
ToolDefinition(
    name="complex_operation",
    description="Performs a complex operation with multiple steps",
    parameters=[
        ToolParameter(
            name="input_data",
            type=ToolParameterType.OBJECT,
            description="Input data in format: {field1: string, field2: number}",
            required=True
        )
    ],
    returns="Result object with 'status' and 'data' fields",
    examples=[
        "complex_operation(input_data={'field1': 'test', 'field2': 42})"
    ]
)
```

### 5. Versioning

Follow semantic versioning for plugins:

```python
PluginMetadata(
    id="my-plugin",
    name="My Plugin",
    version="1.2.3",  # MAJOR.MINOR.PATCH
    # ...
)
```

## Security Considerations

### Plugin Sandboxing

Future enhancement: Implement sandboxed execution:

```python
# Restrict plugin file access
# Limit network access
# Resource quotas (CPU, memory)
# Timeout enforcement
```

### Configuration Security

Never store secrets in plugin metadata:

```python
# ❌ Bad
PluginMetadata(
    id="my-plugin",
    metadata={"api_key": "secret-key"}  # Don't do this
)

# ✓ Good
# Store secrets in config passed to enable_plugin()
manager.enable_plugin("my-plugin", config={
    "api_key": os.getenv("MY_PLUGIN_API_KEY")
})
```

## Testing Plugins

### Unit Tests

```python
import pytest
from my_plugin.plugin import MyPlugin


def test_plugin_metadata():
    plugin = MyPlugin()
    metadata = plugin.get_metadata()

    assert metadata.id == "my-plugin"
    assert metadata.version == "1.0.0"


def test_tool_execution():
    plugin = MyPlugin()

    result = plugin.execute_tool("my_tool", {
        "param1": "test"
    })

    assert result["success"] is True


def test_tool_error_handling():
    plugin = MyPlugin()

    with pytest.raises(ValueError):
        plugin.execute_tool("nonexistent_tool", {})
```

### Integration Tests

```python
def test_plugin_lifecycle():
    manager = PluginManager()

    # Install
    plugin_info = manager.install_plugin(Path("my_plugin"))
    assert plugin_info.status == PluginStatus.INSTALLED

    # Enable
    manager.enable_plugin("my-plugin")
    assert manager.registry.get_plugin("my-plugin").status == PluginStatus.ENABLED

    # Execute
    result = manager.execute_tool("my-plugin", "my_tool", {"param1": "test"})
    assert result is not None

    # Disable
    manager.disable_plugin("my-plugin")
    assert manager.registry.get_plugin("my-plugin").status == PluginStatus.DISABLED

    # Uninstall
    manager.uninstall_plugin("my-plugin")
    assert manager.registry.get_plugin("my-plugin") is None
```

## Future Enhancements

1. **Plugin Marketplace**: Discover and install plugins from repository
2. **Dependency Management**: Automatic installation of plugin dependencies
3. **Plugin Versioning**: Support multiple versions of same plugin
4. **Hot Reloading**: Reload plugins without restarting system
5. **Plugin Templates**: More templates for common plugin types
6. **Sandboxing**: Isolated execution environment for plugins
7. **Plugin Analytics**: Track plugin usage and performance
8. **Plugin UI**: Web interface for plugin management

## API Reference

See `apps/realtime-poc/features/plugin_system.py` for complete API documentation.

### Key Classes

- `PluginManager`: High-level plugin management
- `PluginLoader`: Load plugins from files/directories
- `PluginRegistry`: Plugin metadata and status storage
- `Plugin`: Base class for all plugins
- `ToolDefinition`: Define custom tools
- `ToolParameter`: Define tool parameters

### Key Methods

- `install_plugin()`: Install plugin from source
- `enable_plugin()`: Enable installed plugin
- `disable_plugin()`: Disable enabled plugin
- `uninstall_plugin()`: Remove plugin
- `execute_tool()`: Execute plugin tool
- `get_all_tools()`: Get all enabled tools
- `discover_and_load_all()`: Auto-discover plugins

## Conclusion

The Plugin System & Custom Tools framework enables unlimited extensibility for the Big Three Realtime Agents. Users can create custom tools, integrate third-party services, and share plugins with the community, making the system adaptable to any domain or workflow.
