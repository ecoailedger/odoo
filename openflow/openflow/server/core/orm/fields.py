"""
Field descriptors for ORM models

This module provides field types that can be used to define model attributes.
Fields handle type validation, default values, computation, and database mapping.
"""
from typing import Any, Callable, Optional, Union, List, Tuple
from datetime import date, datetime
from enum import Enum


class Field:
    """
    Base field descriptor for model attributes

    Args:
        string: Human-readable field label
        required: Whether the field must have a value
        readonly: Whether the field can be written to
        default: Default value (can be a callable)
        compute: Method name for computed field
        inverse: Method name for inverse computation
        search: Method name for search implementation
        related: Path to related field (e.g., 'partner_id.name')
        store: Whether computed field should be stored in DB
        depends: List of fields this computed field depends on
        index: Whether to create database index
        copy: Whether to copy field value when duplicating record
        help: Help text for the field
        groups: Comma-separated list of group external IDs that can access this field
    """

    _field_type = 'field'
    _column_type = None  # Will be set by subclasses

    def __init__(
        self,
        string: str = '',
        required: bool = False,
        readonly: bool = False,
        default: Optional[Union[Any, Callable]] = None,
        compute: Optional[str] = None,
        inverse: Optional[str] = None,
        search: Optional[str] = None,
        related: Optional[str] = None,
        store: bool = True,
        depends: Optional[List[str]] = None,
        index: bool = False,
        copy: bool = True,
        help: str = '',
        groups: Optional[str] = None,
        **kwargs
    ):
        self.string = string
        self.required = required
        self.readonly = readonly
        self._default = default
        self.compute = compute
        self.inverse = inverse
        self.search = search
        self.related = related
        self.store = store if not compute else store
        self.depends = depends or []
        self.index = index
        self.copy = copy
        self.help = help
        self.groups = groups  # Comma-separated group external IDs
        self.name = None  # Will be set by metaclass
        self.model_name = None  # Will be set by metaclass
        self.kwargs = kwargs

        # Computed fields must have depends if stored
        if self.compute and not self.related:
            self.store = store
            if self.store and not self.depends:
                raise ValueError(f"Stored computed field must specify depends")

        # Related fields are computed fields
        if self.related:
            if not self.compute:
                self.compute = '_compute_related'
            self.depends = [self.related]

    def __set_name__(self, owner, name):
        """Called when field is assigned to a class"""
        self.name = name
        if hasattr(owner, '_name'):
            self.model_name = owner._name

    def __get__(self, instance, owner):
        """Get field value from instance"""
        if instance is None:
            return self
        return instance._get_field_value(self.name)

    def __set__(self, instance, value):
        """Set field value on instance"""
        if self.readonly and not instance._allow_readonly_write:
            raise ValueError(f"Field '{self.name}' is readonly")
        instance._set_field_value(self.name, value)

    def get_default(self, model):
        """Get default value for this field"""
        if self._default is None:
            return self.get_type_default()
        elif callable(self._default):
            return self._default(model)
        else:
            return self._default

    def get_type_default(self):
        """Get default value based on field type"""
        return None

    def validate(self, value):
        """Validate field value"""
        if self.required and value is None:
            raise ValueError(f"Field '{self.name}' is required")
        return True

    def convert_to_cache(self, value):
        """Convert value for cache storage"""
        return value

    def convert_from_cache(self, value):
        """Convert value from cache"""
        return value

    def convert_to_database(self, value):
        """Convert value for database storage"""
        return value

    def convert_from_database(self, value):
        """Convert value from database"""
        return value


class Char(Field):
    """
    String field with maximum size

    Args:
        size: Maximum string length
        translate: Whether field is translatable
    """
    _field_type = 'char'
    _column_type = 'VARCHAR'

    def __init__(self, size: int = 255, translate: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.translate = translate

    def get_type_default(self):
        return ''

    def validate(self, value):
        super().validate(value)
        if value and len(str(value)) > self.size:
            raise ValueError(f"Field '{self.name}' exceeds maximum size of {self.size}")
        return True


class Text(Field):
    """
    Long text field without size limit

    Args:
        translate: Whether field is translatable
    """
    _field_type = 'text'
    _column_type = 'TEXT'

    def __init__(self, translate: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.translate = translate

    def get_type_default(self):
        return ''


class Integer(Field):
    """Integer number field"""
    _field_type = 'integer'
    _column_type = 'INTEGER'

    def get_type_default(self):
        return 0

    def convert_to_cache(self, value):
        if value is None:
            return None
        return int(value)


class Float(Field):
    """
    Floating point number field

    Args:
        digits: Tuple of (precision, scale) for decimal precision
    """
    _field_type = 'float'
    _column_type = 'DOUBLE PRECISION'

    def __init__(self, digits: Optional[Tuple[int, int]] = None, **kwargs):
        super().__init__(**kwargs)
        self.digits = digits

    def get_type_default(self):
        return 0.0

    def convert_to_cache(self, value):
        if value is None:
            return None
        return float(value)


class Boolean(Field):
    """Boolean field"""
    _field_type = 'boolean'
    _column_type = 'BOOLEAN'

    def get_type_default(self):
        return False

    def convert_to_cache(self, value):
        if value is None:
            return False
        return bool(value)


class Date(Field):
    """Date field (without time)"""
    _field_type = 'date'
    _column_type = 'DATE'

    def convert_to_cache(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return datetime.strptime(value, '%Y-%m-%d').date()
        if isinstance(value, datetime):
            return value.date()
        return value

    def convert_to_database(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, date):
            return value.isoformat()
        return value


class DateTime(Field):
    """DateTime field (with time)"""
    _field_type = 'datetime'
    _column_type = 'TIMESTAMP'

    def convert_to_cache(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            # Try common datetime formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse datetime: {value}")
        return value

    def convert_to_database(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class Binary(Field):
    """Binary data field (files, images, etc.)"""
    _field_type = 'binary'
    _column_type = 'BYTEA'

    def __init__(self, attachment: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.attachment = attachment


class Selection(Field):
    """
    Selection field (dropdown with predefined choices)

    Args:
        selection: List of (value, label) tuples or method name returning such list
    """
    _field_type = 'selection'
    _column_type = 'VARCHAR'

    def __init__(self, selection: Union[List[Tuple[str, str]], str], **kwargs):
        super().__init__(**kwargs)
        self.selection = selection

    def get_selection(self, model):
        """Get selection values"""
        if isinstance(self.selection, str):
            # Selection is a method name
            method = getattr(model, self.selection)
            return method()
        return self.selection

    def validate(self, value):
        super().validate(value)
        if value is not None:
            # Note: We can't validate selection here without model instance
            # Validation will be done at model level
            pass
        return True


class Many2one(Field):
    """
    Many-to-one relationship field

    Args:
        comodel_name: Name of the related model
        ondelete: Action when related record is deleted ('set null', 'restrict', 'cascade')
        domain: Domain filter for related records
    """
    _field_type = 'many2one'
    _column_type = 'INTEGER'

    def __init__(
        self,
        comodel_name: str,
        ondelete: str = 'set null',
        domain: Optional[List] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.ondelete = ondelete
        self.domain = domain or []

    def get_type_default(self):
        return None


class One2many(Field):
    """
    One-to-many relationship field (inverse of Many2one)

    Args:
        comodel_name: Name of the related model
        inverse_name: Name of the Many2one field on related model
        domain: Domain filter for related records
    """
    _field_type = 'one2many'
    _column_type = None  # No column, virtual field

    def __init__(
        self,
        comodel_name: str,
        inverse_name: str,
        domain: Optional[List] = None,
        **kwargs
    ):
        super().__init__(store=False, **kwargs)  # One2many is never stored
        self.comodel_name = comodel_name
        self.inverse_name = inverse_name
        self.domain = domain or []

    def get_type_default(self):
        return []


class Many2many(Field):
    """
    Many-to-many relationship field

    Args:
        comodel_name: Name of the related model
        relation: Name of the intermediate table
        column1: Name of the column referencing this model
        column2: Name of the column referencing the related model
        domain: Domain filter for related records
    """
    _field_type = 'many2many'
    _column_type = None  # Uses junction table

    def __init__(
        self,
        comodel_name: str,
        relation: Optional[str] = None,
        column1: Optional[str] = None,
        column2: Optional[str] = None,
        domain: Optional[List] = None,
        **kwargs
    ):
        super().__init__(store=False, **kwargs)  # Many2many storage is special
        self.comodel_name = comodel_name
        self.relation = relation  # Will be auto-generated if not provided
        self.column1 = column1
        self.column2 = column2
        self.domain = domain or []

    def get_type_default(self):
        return []


# Field type registry for easy lookup
FIELD_TYPES = {
    'char': Char,
    'text': Text,
    'integer': Integer,
    'float': Float,
    'boolean': Boolean,
    'date': Date,
    'datetime': DateTime,
    'binary': Binary,
    'selection': Selection,
    'many2one': Many2one,
    'one2many': One2many,
    'many2many': Many2many,
}
