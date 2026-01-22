"""
Model registry for managing ORM models

The registry maintains a global collection of all models and provides
model lookup and lifecycle management.
"""
from typing import Dict, Type, Optional, Any
import threading


class ModelRegistry:
    """
    Registry for managing all ORM models

    The registry is a singleton that stores all model classes and provides
    lookup functionality. Models are registered automatically via metaclass.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize registry"""
        if self._initialized:
            return

        self._models: Dict[str, Type] = {}
        self._initialized = True

    def register(self, model_name: str, model_class: Type):
        """
        Register a model in the registry

        Args:
            model_name: Unique model name (e.g., 'res.partner')
            model_class: Model class to register

        Raises:
            ValueError: If model name is already registered
        """
        if model_name in self._models:
            # Allow re-registration for model inheritance/extension
            pass
        self._models[model_name] = model_class

    def get(self, model_name: str) -> Optional[Type]:
        """
        Get model class by name

        Args:
            model_name: Model name to lookup

        Returns:
            Model class or None if not found
        """
        return self._models.get(model_name)

    def __getitem__(self, model_name: str) -> Type:
        """
        Get model class by name (raises KeyError if not found)

        Args:
            model_name: Model name to lookup

        Returns:
            Model class

        Raises:
            KeyError: If model not found
        """
        if model_name not in self._models:
            raise KeyError(f"Model '{model_name}' not found in registry")
        return self._models[model_name]

    def __contains__(self, model_name: str) -> bool:
        """Check if model is registered"""
        return model_name in self._models

    def keys(self):
        """Get all registered model names"""
        return self._models.keys()

    def values(self):
        """Get all registered model classes"""
        return self._models.values()

    def items(self):
        """Get all (name, class) pairs"""
        return self._models.items()

    def clear(self):
        """Clear all registered models (useful for testing)"""
        self._models.clear()


# Global registry instance
registry = ModelRegistry()


class Environment:
    """
    Environment encapsulates request-specific context

    The environment stores the database session, user context, and provides
    access to models with that context.
    """

    def __init__(self, session=None, user=None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize environment

        Args:
            session: Database session
            user: Current user
            context: Additional context dictionary
        """
        self.session = session
        self.user = user
        self.context = context or {}
        self._cache = {}

    def __getitem__(self, model_name: str):
        """
        Get model with this environment

        Args:
            model_name: Model name to get

        Returns:
            Model class bound to this environment
        """
        model_class = registry[model_name]
        # Return model bound to this environment
        return model_class.with_env(self)

    def ref(self, xml_id: str):
        """
        Get record by XML ID

        Args:
            xml_id: External identifier (e.g., 'base.user_admin')

        Returns:
            RecordSet for the referenced record
        """
        # This will be implemented when we have external ID support
        raise NotImplementedError("External ID lookup not yet implemented")

    def invalidate_cache(self):
        """Invalidate all cached values"""
        self._cache.clear()


def get_env(session=None, user=None, context=None) -> Environment:
    """
    Get or create environment

    Args:
        session: Database session
        user: Current user
        context: Additional context

    Returns:
        Environment instance
    """
    return Environment(session=session, user=user, context=context)
