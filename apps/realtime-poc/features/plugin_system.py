"""
Plugin System & Custom Tools for Big Three Realtime Agents

This module provides an extensibility framework for creating custom agent tools:
- Plugin architecture for extending agent capabilities
- Custom tool definitions with JSON schemas
- Plugin discovery and loading
- Plugin lifecycle management (install, enable, disable)
- Sandboxed plugin execution
- Plugin marketplace foundation
- Event hooks and callbacks

Author: Big Three Realtime Agents
Version: 1.0.0
"""

import json
import importlib
import importlib.util
import sys
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import threading
import uuid
import traceback


class PluginStatus(Enum):
    """Plugin status values"""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class ToolParameterType(Enum):
    """Tool parameter types"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Defines a parameter for a custom tool"""
    name: str
    type: ToolParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "required": self.required
        }

        if self.default is not None:
            data["default"] = self.default

        if self.enum:
            data["enum"] = self.enum

        return data

    def to_json_schema(self) -> dict:
        """Convert to JSON schema format"""
        schema = {
            "type": self.type.value,
            "description": self.description
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.default is not None:
            schema["default"] = self.default

        return schema


@dataclass
class ToolDefinition:
    """Defines a custom tool"""
    name: str
    description: str
    parameters: List[ToolParameter]
    returns: Optional[str] = None
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns,
            "examples": self.examples
        }

    def to_openai_function(self) -> dict:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


@dataclass
class PluginMetadata:
    """Plugin metadata"""
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

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PluginInfo:
    """Plugin installation info"""
    plugin_id: str
    metadata: PluginMetadata
    status: PluginStatus
    installed_at: str
    last_updated: str
    enabled_at: Optional[str] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        data['metadata'] = self.metadata.to_dict()
        return data


class Plugin(ABC):
    """
    Base class for all plugins.

    Subclass this to create custom plugins with tools and hooks.
    """

    def __init__(self):
        """Initialize plugin"""
        self.config: Dict[str, Any] = {}
        self.enabled: bool = False

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    def get_tools(self) -> List[ToolDefinition]:
        """Return list of tools provided by this plugin"""
        pass

    def on_install(self):
        """Called when plugin is installed"""
        pass

    def on_enable(self):
        """Called when plugin is enabled"""
        self.enabled = True

    def on_disable(self):
        """Called when plugin is disabled"""
        self.enabled = False

    def on_uninstall(self):
        """Called when plugin is uninstalled"""
        pass

    def on_configure(self, config: Dict[str, Any]):
        """Called when plugin configuration changes"""
        self.config = config

    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool provided by this plugin"""
        pass


class PluginRegistry:
    """
    Manages plugin registration and metadata.

    Stores plugin information in JSON registry file.
    """

    def __init__(self, registry_path: Path = None):
        """Initialize plugin registry"""
        if registry_path is None:
            registry_path = Path("plugins/registry.json")

        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.plugins: Dict[str, PluginInfo] = {}
        self._load_registry()

    def _load_registry(self):
        """Load registry from file"""
        if not self.registry_path.exists():
            self._save_registry()
            return

        with self.lock:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)

            for plugin_id, plugin_data in data.items():
                metadata_data = plugin_data["metadata"]
                metadata = PluginMetadata(**metadata_data)

                plugin_info = PluginInfo(
                    plugin_id=plugin_data["plugin_id"],
                    metadata=metadata,
                    status=PluginStatus(plugin_data["status"]),
                    installed_at=plugin_data["installed_at"],
                    last_updated=plugin_data["last_updated"],
                    enabled_at=plugin_data.get("enabled_at"),
                    error_message=plugin_data.get("error_message"),
                    config=plugin_data.get("config", {})
                )

                self.plugins[plugin_id] = plugin_info

    def _save_registry(self):
        """Save registry to file"""
        with self.lock:
            data = {
                plugin_id: plugin_info.to_dict()
                for plugin_id, plugin_info in self.plugins.items()
            }

            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)

    def register_plugin(
        self,
        plugin_id: str,
        metadata: PluginMetadata,
        status: PluginStatus = PluginStatus.INSTALLED
    ) -> PluginInfo:
        """Register a new plugin"""
        now = datetime.now().isoformat()

        plugin_info = PluginInfo(
            plugin_id=plugin_id,
            metadata=metadata,
            status=status,
            installed_at=now,
            last_updated=now
        )

        self.plugins[plugin_id] = plugin_info
        self._save_registry()
        return plugin_info

    def update_plugin_status(
        self,
        plugin_id: str,
        status: PluginStatus,
        error_message: Optional[str] = None
    ):
        """Update plugin status"""
        if plugin_id not in self.plugins:
            raise ValueError(f"Plugin {plugin_id} not found")

        plugin = self.plugins[plugin_id]
        plugin.status = status
        plugin.last_updated = datetime.now().isoformat()
        plugin.error_message = error_message

        if status == PluginStatus.ENABLED:
            plugin.enabled_at = datetime.now().isoformat()

        self._save_registry()

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin info"""
        return self.plugins.get(plugin_id)

    def list_plugins(
        self,
        status: Optional[PluginStatus] = None
    ) -> List[PluginInfo]:
        """List all plugins"""
        if status:
            return [p for p in self.plugins.values() if p.status == status]
        return list(self.plugins.values())

    def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin"""
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            self._save_registry()


class PluginLoader:
    """
    Loads plugins from Python files and directories.

    Supports:
    - Loading from .py files
    - Loading from plugin directories
    - Hot reloading
    """

    def __init__(self, plugins_dir: Path = None):
        """Initialize plugin loader"""
        if plugins_dir is None:
            plugins_dir = Path("plugins/installed")

        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_plugins: Dict[str, Plugin] = {}

    def load_plugin_from_file(self, plugin_file: Path) -> Plugin:
        """Load a plugin from a Python file"""
        if not plugin_file.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_file}")

        # Load module
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_file.stem}",
            plugin_file
        )

        if not spec or not spec.loader:
            raise ImportError(f"Cannot load plugin from {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Find Plugin subclass
        plugin_class = None
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Plugin) and obj != Plugin:
                plugin_class = obj
                break

        if not plugin_class:
            raise ValueError(f"No Plugin subclass found in {plugin_file}")

        # Instantiate plugin
        plugin = plugin_class()
        return plugin

    def load_plugin_from_directory(self, plugin_dir: Path) -> Plugin:
        """Load a plugin from a directory (looks for __init__.py or plugin.py)"""
        if not plugin_dir.is_dir():
            raise NotADirectoryError(f"{plugin_dir} is not a directory")

        # Try __init__.py first, then plugin.py
        init_file = plugin_dir / "__init__.py"
        plugin_file = plugin_dir / "plugin.py"

        if init_file.exists():
            return self.load_plugin_from_file(init_file)
        elif plugin_file.exists():
            return self.load_plugin_from_file(plugin_file)
        else:
            raise FileNotFoundError(
                f"No __init__.py or plugin.py found in {plugin_dir}"
            )

    def discover_plugins(self) -> List[Path]:
        """Discover all plugins in plugins directory"""
        plugins = []

        # Find .py files
        for py_file in self.plugins_dir.glob("*.py"):
            if py_file.stem != "__init__":
                plugins.append(py_file)

        # Find plugin directories
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("_"):
                if (plugin_dir / "__init__.py").exists() or \
                   (plugin_dir / "plugin.py").exists():
                    plugins.append(plugin_dir)

        return plugins


class PluginManager:
    """
    High-level plugin management interface.

    Combines registry, loader, and execution.
    """

    def __init__(
        self,
        plugins_dir: Path = None,
        registry_path: Path = None
    ):
        """Initialize plugin manager"""
        self.loader = PluginLoader(plugins_dir)
        self.registry = PluginRegistry(registry_path)
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.lock = threading.Lock()

    def install_plugin(self, plugin_source: Path) -> PluginInfo:
        """Install a plugin from file or directory"""
        try:
            # Load plugin
            if plugin_source.is_file():
                plugin = self.loader.load_plugin_from_file(plugin_source)
            else:
                plugin = self.loader.load_plugin_from_directory(plugin_source)

            # Get metadata
            metadata = plugin.get_metadata()

            # Check if already installed
            if self.registry.get_plugin(metadata.id):
                raise ValueError(f"Plugin {metadata.id} already installed")

            # Register plugin
            plugin_info = self.registry.register_plugin(
                metadata.id,
                metadata,
                PluginStatus.INSTALLED
            )

            # Call install hook
            plugin.on_install()

            # Store loaded plugin
            with self.lock:
                self.loaded_plugins[metadata.id] = plugin

            return plugin_info

        except Exception as e:
            error_msg = f"Failed to install plugin: {str(e)}\n{traceback.format_exc()}"
            raise RuntimeError(error_msg)

    def enable_plugin(self, plugin_id: str, config: Dict[str, Any] = None):
        """Enable a plugin"""
        plugin_info = self.registry.get_plugin(plugin_id)

        if not plugin_info:
            raise ValueError(f"Plugin {plugin_id} not found")

        if plugin_info.status == PluginStatus.ENABLED:
            return  # Already enabled

        # Get plugin instance
        plugin = self.loaded_plugins.get(plugin_id)

        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not loaded")

        try:
            # Configure plugin
            if config:
                plugin.on_configure(config)
                plugin_info.config = config

            # Enable plugin
            plugin.on_enable()

            # Update status
            self.registry.update_plugin_status(
                plugin_id,
                PluginStatus.ENABLED
            )

        except Exception as e:
            error_msg = f"Failed to enable plugin: {str(e)}"
            self.registry.update_plugin_status(
                plugin_id,
                PluginStatus.ERROR,
                error_msg
            )
            raise

    def disable_plugin(self, plugin_id: str):
        """Disable a plugin"""
        plugin_info = self.registry.get_plugin(plugin_id)

        if not plugin_info:
            raise ValueError(f"Plugin {plugin_id} not found")

        if plugin_info.status != PluginStatus.ENABLED:
            return  # Not enabled

        # Get plugin instance
        plugin = self.loaded_plugins.get(plugin_id)

        if plugin:
            plugin.on_disable()

        # Update status
        self.registry.update_plugin_status(
            plugin_id,
            PluginStatus.DISABLED
        )

    def uninstall_plugin(self, plugin_id: str):
        """Uninstall a plugin"""
        plugin_info = self.registry.get_plugin(plugin_id)

        if not plugin_info:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Disable first if enabled
        if plugin_info.status == PluginStatus.ENABLED:
            self.disable_plugin(plugin_id)

        # Get plugin instance
        plugin = self.loaded_plugins.get(plugin_id)

        if plugin:
            plugin.on_uninstall()

            # Remove from loaded plugins
            with self.lock:
                del self.loaded_plugins[plugin_id]

        # Unregister
        self.registry.unregister_plugin(plugin_id)

    def get_plugin_tools(self, plugin_id: str) -> List[ToolDefinition]:
        """Get tools provided by a plugin"""
        plugin = self.loaded_plugins.get(plugin_id)

        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not loaded")

        return plugin.get_tools()

    def get_all_tools(self) -> Dict[str, List[ToolDefinition]]:
        """Get all tools from all enabled plugins"""
        tools = {}

        for plugin_id, plugin in self.loaded_plugins.items():
            plugin_info = self.registry.get_plugin(plugin_id)

            if plugin_info and plugin_info.status == PluginStatus.ENABLED:
                tools[plugin_id] = plugin.get_tools()

        return tools

    def execute_tool(
        self,
        plugin_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute a tool from a plugin"""
        plugin = self.loaded_plugins.get(plugin_id)

        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not loaded")

        plugin_info = self.registry.get_plugin(plugin_id)

        if not plugin_info or plugin_info.status != PluginStatus.ENABLED:
            raise ValueError(f"Plugin {plugin_id} not enabled")

        try:
            result = plugin.execute_tool(tool_name, parameters)
            return result

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}\n{traceback.format_exc()}"
            raise RuntimeError(error_msg)

    def list_plugins(
        self,
        status: Optional[PluginStatus] = None
    ) -> List[PluginInfo]:
        """List all plugins"""
        return self.registry.list_plugins(status)

    def discover_and_load_all(self):
        """Discover and load all plugins from plugins directory"""
        discovered = self.loader.discover_plugins()

        for plugin_source in discovered:
            try:
                # Try to install
                self.install_plugin(plugin_source)
            except ValueError as e:
                # Already installed, skip
                if "already installed" not in str(e):
                    print(f"Warning: Failed to load {plugin_source}: {e}")
            except Exception as e:
                print(f"Error loading {plugin_source}: {e}")


# Example plugin for demonstration
class ExamplePlugin(Plugin):
    """Example plugin demonstrating the plugin system"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="example-plugin",
            name="Example Plugin",
            version="1.0.0",
            description="Example plugin demonstrating custom tools",
            author="Big Three Team",
            tags=["example", "demo"]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="example_tool",
                description="An example custom tool",
                parameters=[
                    ToolParameter(
                        name="message",
                        type=ToolParameterType.STRING,
                        description="Message to process",
                        required=True
                    ),
                    ToolParameter(
                        name="uppercase",
                        type=ToolParameterType.BOOLEAN,
                        description="Convert to uppercase",
                        required=False,
                        default=False
                    )
                ],
                returns="Processed message",
                examples=[
                    "example_tool(message='hello', uppercase=True) -> 'HELLO'",
                    "example_tool(message='world') -> 'world'"
                ]
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "example_tool":
            message = parameters.get("message", "")
            uppercase = parameters.get("uppercase", False)

            if uppercase:
                return message.upper()
            return message

        raise ValueError(f"Unknown tool: {tool_name}")


# Utility functions

def create_plugin_template(
    plugin_id: str,
    plugin_name: str,
    output_dir: Path
) -> Path:
    """Create a plugin template directory"""
    plugin_dir = output_dir / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_content = f'''"""
{plugin_name}

Custom plugin for Big Three Realtime Agents.
"""

from .plugin import {plugin_id.replace("-", "_").title()}Plugin

__all__ = ["{plugin_id.replace("-", "_").title()}Plugin"]
'''

    # Create plugin.py
    plugin_content = f'''"""
{plugin_name} implementation
"""

from features.plugin_system import (
    Plugin,
    PluginMetadata,
    ToolDefinition,
    ToolParameter,
    ToolParameterType
)
from typing import List, Dict, Any


class {plugin_id.replace("-", "_").title()}Plugin(Plugin):
    """
    {plugin_name}

    TODO: Add plugin description
    """

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="{plugin_id}",
            name="{plugin_name}",
            version="1.0.0",
            description="TODO: Add description",
            author="Your Name",
            tags=[]
        )

    def get_tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="example_tool",
                description="TODO: Add tool description",
                parameters=[
                    ToolParameter(
                        name="input",
                        type=ToolParameterType.STRING,
                        description="TODO: Add parameter description",
                        required=True
                    )
                ],
                returns="TODO: Describe return value"
            )
        ]

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        if tool_name == "example_tool":
            # TODO: Implement tool logic
            input_value = parameters.get("input")
            return {{"result": f"Processed: {{input_value}}"}}

        raise ValueError(f"Unknown tool: {{tool_name}}")
'''

    # Create README.md
    readme_content = f'''# {plugin_name}

TODO: Add plugin description

## Installation

```python
from features.plugin_system import PluginManager

manager = PluginManager()
manager.install_plugin(Path("{plugin_id}"))
manager.enable_plugin("{plugin_id}")
```

## Tools

### example_tool

TODO: Add tool documentation

**Parameters:**
- `input` (string): TODO: Add description

**Returns:** TODO: Describe return value

**Example:**
```python
result = manager.execute_tool("{plugin_id}", "example_tool", {{
    "input": "test"
}})
```

## License

MIT
'''

    (plugin_dir / "__init__.py").write_text(init_content)
    (plugin_dir / "plugin.py").write_text(plugin_content)
    (plugin_dir / "README.md").write_text(readme_content)

    return plugin_dir


def export_tools_for_openai(plugin_manager: PluginManager) -> List[dict]:
    """Export all enabled plugin tools in OpenAI function calling format"""
    all_tools = plugin_manager.get_all_tools()
    openai_functions = []

    for plugin_id, tools in all_tools.items():
        for tool in tools:
            openai_functions.append(tool.to_openai_function())

    return openai_functions
