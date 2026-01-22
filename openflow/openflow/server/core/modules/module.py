"""
Module and Manifest Definitions

Defines the structure of OpenFlow modules and their manifest files.
"""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum


class ModuleState(str, Enum):
    """Module installation states"""
    UNINSTALLED = "uninstalled"
    INSTALLED = "installed"
    TO_INSTALL = "to install"
    TO_UPGRADE = "to upgrade"
    TO_REMOVE = "to remove"


@dataclass
class ModuleManifest:
    """
    Module manifest structure following Odoo's __manifest__.py format

    Example:
        {
            'name': 'Base Module',
            'version': '1.0',
            'category': 'Hidden',
            'summary': 'Core models and infrastructure',
            'description': '''Long description here''',
            'depends': [],
            'data': ['security/ir.model.access.csv', 'views/views.xml'],
            'installable': True,
            'auto_install': False,
            'application': False,
        }
    """
    name: str
    version: str = "1.0"
    category: str = "Uncategorized"
    summary: str = ""
    description: str = ""
    author: str = "OpenFlow"
    website: str = ""
    depends: List[str] = field(default_factory=list)
    data: List[str] = field(default_factory=list)
    demo: List[str] = field(default_factory=list)
    installable: bool = True
    auto_install: bool = False
    application: bool = False
    license: str = "LGPL-3"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleManifest':
        """Create manifest from dictionary"""
        # Filter only known fields
        valid_fields = {
            f.name for f in cls.__dataclass_fields__.values()
        }
        filtered_data = {
            k: v for k, v in data.items() if k in valid_fields
        }
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'category': self.category,
            'summary': self.summary,
            'description': self.description,
            'author': self.author,
            'website': self.website,
            'depends': self.depends,
            'data': self.data,
            'demo': self.demo,
            'installable': self.installable,
            'auto_install': self.auto_install,
            'application': self.application,
            'license': self.license,
        }


@dataclass
class Module:
    """Represents an OpenFlow module/addon"""
    name: str
    path: Path
    manifest: ModuleManifest
    state: ModuleState = ModuleState.UNINSTALLED

    @property
    def module_path(self) -> Path:
        """Get the module directory path"""
        return self.path

    @property
    def models_path(self) -> Optional[Path]:
        """Get the models directory if it exists"""
        models_dir = self.path / "models"
        return models_dir if models_dir.exists() else None

    @property
    def views_path(self) -> Optional[Path]:
        """Get the views directory if it exists"""
        views_dir = self.path / "views"
        return views_dir if views_dir.exists() else None

    @property
    def security_path(self) -> Optional[Path]:
        """Get the security directory if it exists"""
        security_dir = self.path / "security"
        return security_dir if security_dir.exists() else None

    @property
    def data_path(self) -> Optional[Path]:
        """Get the data directory if it exists"""
        data_dir = self.path / "data"
        return data_dir if data_dir.exists() else None

    @property
    def controllers_path(self) -> Optional[Path]:
        """Get the controllers directory if it exists"""
        controllers_dir = self.path / "controllers"
        return controllers_dir if controllers_dir.exists() else None

    @property
    def static_path(self) -> Optional[Path]:
        """Get the static directory if it exists"""
        static_dir = self.path / "static"
        return static_dir if static_dir.exists() else None

    @classmethod
    def load_from_path(cls, module_path: Path) -> 'Module':
        """
        Load a module from a directory path

        Args:
            module_path: Path to the module directory

        Returns:
            Module instance

        Raises:
            FileNotFoundError: If __manifest__.py doesn't exist
            ValueError: If manifest is invalid
        """
        manifest_file = module_path / "__manifest__.py"

        if not manifest_file.exists():
            raise FileNotFoundError(
                f"Module at {module_path} is missing __manifest__.py"
            )

        # Read and parse the manifest file
        manifest_dict = cls._parse_manifest(manifest_file)
        manifest = ModuleManifest.from_dict(manifest_dict)

        # Validate manifest
        if not manifest.name:
            raise ValueError(
                f"Module at {module_path} has no 'name' in manifest"
            )

        module_name = module_path.name

        return cls(
            name=module_name,
            path=module_path,
            manifest=manifest,
        )

    @staticmethod
    def _parse_manifest(manifest_file: Path) -> Dict[str, Any]:
        """
        Parse __manifest__.py file safely

        Args:
            manifest_file: Path to __manifest__.py

        Returns:
            Dictionary with manifest data
        """
        with open(manifest_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the Python file safely
        try:
            tree = ast.parse(content)

            # Find the dictionary assignment (usually the entire file is a dict)
            for node in ast.walk(tree):
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
                    return ast.literal_eval(node.value)
                elif isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Dict):
                        return ast.literal_eval(node.value)

            # If no dict found, try to evaluate the entire content
            return ast.literal_eval(content)
        except (SyntaxError, ValueError) as e:
            raise ValueError(
                f"Invalid manifest file {manifest_file}: {e}"
            )

    def __repr__(self) -> str:
        return f"<Module {self.name} ({self.state})>"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if isinstance(other, Module):
            return self.name == other.name
        return False
