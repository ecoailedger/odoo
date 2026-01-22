"""
OpenFlow Module System

Provides automatic module loading, dependency resolution, and module lifecycle management.
"""
from .loader import ModuleLoader, ModuleGraph
from .module import Module, ModuleManifest, ModuleState
from .registry import ModuleRegistry, module_registry
from .data_loader import DataLoader, ExternalIdManager

__all__ = [
    'ModuleLoader',
    'ModuleGraph',
    'Module',
    'ModuleManifest',
    'ModuleState',
    'ModuleRegistry',
    'module_registry',
    'DataLoader',
    'ExternalIdManager',
]
