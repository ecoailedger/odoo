"""
View System

Provides XML-based view definitions for UI rendering.
"""
from .parser import ViewParser
from .inheritance import ViewInheritance
from .validator import ViewValidator
from .renderer import ViewRenderer

__all__ = ['ViewParser', 'ViewInheritance', 'ViewValidator', 'ViewRenderer']
