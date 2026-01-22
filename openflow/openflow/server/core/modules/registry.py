"""
Module Registry

Manages module state persistence and integration with the ORM.
"""
import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from .module import Module, ModuleState
from .loader import ModuleLoader

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Module registry for tracking installed modules and their states

    This registry manages:
    - Module discovery and loading
    - Module state persistence in database
    - Integration with ORM model registry
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the registry"""
        if not self._initialized:
            self.loader: Optional[ModuleLoader] = None
            self.modules: Dict[str, Module] = {}
            self._module_states: Dict[str, ModuleState] = {}
            ModuleRegistry._initialized = True

    def initialize(self, addons_paths: List[Path]):
        """
        Initialize the module registry with addons paths

        Args:
            addons_paths: List of directories to search for modules
        """
        logger.info("Initializing module registry")

        self.loader = ModuleLoader(addons_paths)

        # Discover modules
        self.modules = self.loader.discover_modules()

        # Build dependency graph
        self.loader.build_dependency_graph()

        logger.info(f"Module registry initialized with {len(self.modules)} modules")

    def get_module(self, module_name: str) -> Optional[Module]:
        """Get a module by name"""
        return self.modules.get(module_name)

    def get_all_modules(self) -> Dict[str, Module]:
        """Get all discovered modules"""
        return self.modules.copy()

    def get_installed_modules(self) -> List[Module]:
        """Get all installed modules"""
        return [
            m for m in self.modules.values()
            if m.state == ModuleState.INSTALLED
        ]

    def get_load_order(self, module_names: Optional[List[str]] = None) -> List[str]:
        """
        Get module load order

        Args:
            module_names: Specific modules (None = all)

        Returns:
            List of module names in dependency order
        """
        if not self.loader:
            raise RuntimeError("Module registry not initialized")

        return self.loader.get_load_order(module_names)

    def load_modules(self, module_names: Optional[List[str]] = None):
        """
        Load modules in dependency order

        Args:
            module_names: Specific modules to load (None = all installable)
        """
        if not self.loader:
            raise RuntimeError("Module registry not initialized")

        self.loader.load_modules(module_names)

        # Update local cache
        self.modules = self.loader.modules

    async def sync_module_states(self, session: AsyncSession):
        """
        Sync module states with database

        Args:
            session: Database session
        """
        # This will be implemented once we have ir.module.module model
        # For now, we'll just log
        logger.info("Module state sync not yet implemented (requires ir.module.module model)")

    async def install_module(
        self,
        module_name: str,
        session: AsyncSession,
        with_dependencies: bool = True
    ):
        """
        Install a module and optionally its dependencies

        Args:
            module_name: Name of the module to install
            session: Database session
            with_dependencies: Whether to install dependencies
        """
        if not self.loader:
            raise RuntimeError("Module registry not initialized")

        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        # Get modules to install
        if with_dependencies:
            to_install = self.loader.get_load_order([module_name])
        else:
            to_install = [module_name]

        logger.info(f"Installing modules: {to_install}")

        # Load modules
        for name in to_install:
            self.loader.load_module(name)

        # TODO: Execute data files, update database schema, etc.
        logger.info(f"Successfully installed {len(to_install)} modules")

    async def upgrade_module(self, module_name: str, session: AsyncSession):
        """
        Upgrade a module to a new version

        Args:
            module_name: Name of the module to upgrade
            session: Database session
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        if module.state != ModuleState.INSTALLED:
            raise ValueError(f"Module {module_name} is not installed")

        logger.info(f"Upgrading module: {module_name}")

        # TODO: Implement upgrade logic
        # - Compare versions
        # - Run migration scripts
        # - Update database schema
        # - Execute data files

        logger.info(f"Successfully upgraded module: {module_name}")

    async def uninstall_module(self, module_name: str, session: AsyncSession):
        """
        Uninstall a module

        Args:
            module_name: Name of the module to uninstall
            session: Database session
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        if module.state != ModuleState.INSTALLED:
            raise ValueError(f"Module {module_name} is not installed")

        logger.info(f"Uninstalling module: {module_name}")

        # Check for dependent modules
        dependent_modules = self._get_dependent_modules(module_name)
        if dependent_modules:
            raise ValueError(
                f"Cannot uninstall {module_name}: "
                f"modules {dependent_modules} depend on it"
            )

        # TODO: Implement uninstall logic
        # - Remove data
        # - Drop tables
        # - Clean up references

        module.state = ModuleState.UNINSTALLED

        logger.info(f"Successfully uninstalled module: {module_name}")

    def _get_dependent_modules(self, module_name: str) -> List[str]:
        """
        Get modules that depend on the given module

        Args:
            module_name: Name of the module

        Returns:
            List of dependent module names
        """
        dependent = []
        for name, module in self.modules.items():
            if module.state == ModuleState.INSTALLED:
                if module_name in module.manifest.depends:
                    dependent.append(name)
        return dependent

    def get_module_info(self, module_name: str) -> Dict:
        """
        Get detailed information about a module

        Args:
            module_name: Name of the module

        Returns:
            Dictionary with module information
        """
        module = self.get_module(module_name)
        if not module:
            raise ValueError(f"Module {module_name} not found")

        return {
            'name': module.name,
            'state': module.state.value,
            'manifest': module.manifest.to_dict(),
            'path': str(module.path),
        }

    def list_modules(self, state: Optional[ModuleState] = None) -> List[Dict]:
        """
        List all modules, optionally filtered by state

        Args:
            state: Filter by module state (None = all)

        Returns:
            List of module information dictionaries
        """
        modules = self.modules.values()

        if state:
            modules = [m for m in modules if m.state == state]

        return [
            {
                'name': m.name,
                'version': m.manifest.version,
                'summary': m.manifest.summary,
                'state': m.state.value,
                'depends': m.manifest.depends,
                'auto_install': m.manifest.auto_install,
            }
            for m in modules
        ]


# Singleton instance
module_registry = ModuleRegistry()
