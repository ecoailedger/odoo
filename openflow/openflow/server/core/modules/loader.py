"""
Module Loader and Dependency Resolver

Handles module discovery, dependency resolution, and loading order computation.
"""
import importlib
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

from .module import Module, ModuleState

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    pass


class MissingDependencyError(Exception):
    """Raised when a required dependency is missing"""
    pass


class ModuleGraph:
    """
    Dependency graph for modules with topological sort support

    Uses Kahn's algorithm for topological sorting to resolve dependencies.
    """

    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.in_degree: Dict[str, int] = defaultdict(int)
        self.modules: Dict[str, Module] = {}

    def add_module(self, module: Module):
        """Add a module to the graph"""
        self.modules[module.name] = module

        # Initialize the node if not exists
        if module.name not in self.graph:
            self.graph[module.name] = set()
            self.in_degree[module.name] = 0

        # Add dependencies
        for dep in module.manifest.depends:
            self.add_dependency(dep, module.name)

    def add_dependency(self, from_module: str, to_module: str):
        """
        Add a dependency edge: from_module -> to_module
        (to_module depends on from_module)
        """
        if to_module not in self.graph[from_module]:
            self.graph[from_module].add(to_module)
            self.in_degree[to_module] += 1

    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm

        Returns:
            List of module names in load order

        Raises:
            CircularDependencyError: If circular dependencies detected
            MissingDependencyError: If a dependency is missing
        """
        # Verify all dependencies exist
        for module_name, module in self.modules.items():
            for dep in module.manifest.depends:
                if dep not in self.modules:
                    raise MissingDependencyError(
                        f"Module '{module_name}' depends on '{dep}' which is not available"
                    )

        # Create a copy of in_degree for processing
        in_degree_copy = self.in_degree.copy()
        queue = deque()

        # Find all nodes with no incoming edges
        for node in self.graph:
            if in_degree_copy[node] == 0:
                queue.append(node)

        result = []

        while queue:
            # Remove a node from the queue
            node = queue.popleft()
            result.append(node)

            # For each neighbor of the removed node
            for neighbor in self.graph[node]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(result) != len(self.graph):
            # Find the cycle
            remaining = set(self.graph.keys()) - set(result)
            raise CircularDependencyError(
                f"Circular dependency detected involving modules: {remaining}"
            )

        return result

    def get_dependency_chain(self, module_name: str) -> List[str]:
        """
        Get all dependencies of a module in load order

        Args:
            module_name: Name of the module

        Returns:
            List of module names including dependencies in load order
        """
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' not found")

        # Build subgraph with only relevant modules
        visited = set()
        to_visit = [module_name]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)

            if current in self.modules:
                for dep in self.modules[current].manifest.depends:
                    to_visit.append(dep)

        # Create a subgraph and sort
        subgraph = ModuleGraph()
        for name in visited:
            if name in self.modules:
                subgraph.add_module(self.modules[name])

        return subgraph.topological_sort()


class ModuleLoader:
    """
    Module loader with automatic discovery and dependency resolution

    Discovers modules in addons paths, resolves dependencies,
    and loads them in the correct order.
    """

    def __init__(self, addons_paths: Optional[List[Path]] = None):
        """
        Initialize the module loader

        Args:
            addons_paths: List of paths to search for addons
        """
        self.addons_paths = addons_paths or []
        self.modules: Dict[str, Module] = {}
        self.graph = ModuleGraph()
        self._loaded_modules: Set[str] = set()

    def add_addons_path(self, path: Path):
        """Add an addons directory to search"""
        if path not in self.addons_paths:
            self.addons_paths.append(path)

    def discover_modules(self) -> Dict[str, Module]:
        """
        Discover all modules in addons paths

        Returns:
            Dictionary mapping module names to Module instances
        """
        discovered = {}

        for addons_path in self.addons_paths:
            if not addons_path.exists():
                logger.warning(f"Addons path does not exist: {addons_path}")
                continue

            logger.info(f"Discovering modules in: {addons_path}")

            for item in addons_path.iterdir():
                if not item.is_dir():
                    continue

                # Skip hidden directories and __pycache__
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue

                # Check for __manifest__.py
                manifest_file = item / "__manifest__.py"
                if not manifest_file.exists():
                    continue

                try:
                    module = Module.load_from_path(item)

                    # Only add installable modules
                    if not module.manifest.installable:
                        logger.info(f"Skipping non-installable module: {module.name}")
                        continue

                    discovered[module.name] = module
                    logger.info(f"Discovered module: {module.name} v{module.manifest.version}")

                except Exception as e:
                    logger.error(f"Failed to load module from {item}: {e}")

        self.modules.update(discovered)
        return discovered

    def build_dependency_graph(self):
        """Build the dependency graph from discovered modules"""
        self.graph = ModuleGraph()

        for module in self.modules.values():
            self.graph.add_module(module)

        logger.info(f"Built dependency graph for {len(self.modules)} modules")

    def get_load_order(self, module_names: Optional[List[str]] = None) -> List[str]:
        """
        Get the load order for modules

        Args:
            module_names: Specific modules to load (None = all installable modules)

        Returns:
            List of module names in load order

        Raises:
            CircularDependencyError: If circular dependencies detected
            MissingDependencyError: If a dependency is missing
        """
        if module_names is None:
            # Load all modules
            return self.graph.topological_sort()
        else:
            # Load only specified modules and their dependencies
            all_modules = set()
            for name in module_names:
                chain = self.graph.get_dependency_chain(name)
                all_modules.update(chain)

            # Create subgraph
            subgraph = ModuleGraph()
            for name in all_modules:
                if name in self.modules:
                    subgraph.add_module(self.modules[name])

            return subgraph.topological_sort()

    def load_module(self, module_name: str) -> Module:
        """
        Load a single module (import its Python code)

        Args:
            module_name: Name of the module to load

        Returns:
            The loaded Module instance
        """
        if module_name in self._loaded_modules:
            logger.debug(f"Module {module_name} already loaded")
            return self.modules[module_name]

        module = self.modules.get(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        logger.info(f"Loading module: {module_name}")

        try:
            # Add the parent directory to sys.path if not already there
            parent_path = str(module.path.parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)

            # Import the module package
            # This will execute __init__.py which should import models
            module_package = importlib.import_module(module_name)

            # Mark as loaded
            self._loaded_modules.add(module_name)
            module.state = ModuleState.INSTALLED

            logger.info(f"Successfully loaded module: {module_name}")

            return module

        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")
            raise

    def load_modules(self, module_names: Optional[List[str]] = None):
        """
        Load modules in dependency order

        Args:
            module_names: Specific modules to load (None = all)
        """
        # Get load order
        load_order = self.get_load_order(module_names)

        logger.info(f"Loading {len(load_order)} modules in order: {load_order}")

        # Load each module
        for module_name in load_order:
            self.load_module(module_name)

        logger.info(f"Successfully loaded {len(load_order)} modules")

    def get_module(self, module_name: str) -> Optional[Module]:
        """Get a module by name"""
        return self.modules.get(module_name)

    def get_modules_to_install(self) -> List[Module]:
        """Get all modules marked for installation"""
        return [
            m for m in self.modules.values()
            if m.state == ModuleState.TO_INSTALL
        ]

    def get_auto_install_modules(self) -> List[Module]:
        """Get all modules marked for auto-installation"""
        return [
            m for m in self.modules.values()
            if m.manifest.auto_install and m.state == ModuleState.UNINSTALLED
        ]
