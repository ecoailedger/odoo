"""
Base Model class and metaclass for ORM

Models are defined as Python classes with field descriptors.
The metaclass handles model registration, field collection, and table creation.
"""
from typing import Any, Dict, List, Optional, Type, Union
import logging
from sqlalchemy import text, Table, Column, Integer, String, Text as SQLText, \
    Float as SQLFloat, Boolean as SQLBoolean, Date as SQLDate, DateTime as SQLDateTime, \
    LargeBinary, ForeignKey, MetaData, Index
from sqlalchemy.ext.asyncio import AsyncSession

from .fields import Field, Char, Text, Integer as IntegerField, Float, Boolean, \
    Date, DateTime, Binary, Selection, Many2one, One2many, Many2many
from .recordset import RecordSet
from .registry import registry, Environment
from .domain import domain_to_sql

logger = logging.getLogger(__name__)


class ModelMetaclass(type):
    """
    Metaclass for ORM models

    Handles:
    - Field collection and setup
    - Model registration in registry
    - Table schema generation
    - Inheritance setup
    """

    def __new__(mcs, name, bases, attrs):
        """Create new model class"""
        # Create class
        cls = super().__new__(mcs, name, bases, attrs)

        # Skip Model base class itself
        if name == 'Model':
            return cls

        # Get model name
        model_name = attrs.get('_name')
        if not model_name:
            # Auto-generate from class name if not specified
            model_name = name.lower()
            cls._name = model_name

        # Collect fields from class and bases
        fields = {}
        for base in reversed(bases):
            if hasattr(base, '_fields'):
                fields.update(base._fields)

        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, Field):
                attr_value.name = attr_name
                attr_value.model_name = model_name
                fields[attr_name] = attr_value

        cls._fields = fields

        # Add 'id' field if not present
        if 'id' not in cls._fields:
            id_field = IntegerField(string='ID', required=True, readonly=True)
            id_field.name = 'id'
            id_field.model_name = model_name
            cls._fields['id'] = id_field

        # Register model
        registry.register(model_name, cls)

        return cls


class Model(metaclass=ModelMetaclass):
    """
    Base class for all ORM models

    Models represent database tables and provide CRUD operations.
    Records are accessed through RecordSet objects.

    Class attributes:
        _name: Model name (e.g., 'res.partner')
        _table: Database table name (auto-generated if not specified)
        _description: Human-readable description
        _inherit: Parent model(s) for inheritance
        _inherits: Delegation inheritance
        _order: Default order for search results
        _rec_name: Field to use for record display name

    Example:
        class Partner(Model):
            _name = 'res.partner'
            _description = 'Partner'

            name = Char(string='Name', required=True)
            email = Char(string='Email')
            active = Boolean(string='Active', default=True)
    """

    _name: str = None
    _table: str = None
    _description: str = ''
    _inherit: Union[str, List[str]] = None
    _inherits: Dict[str, str] = {}
    _order: str = 'id'
    _rec_name: str = 'name'

    _fields: Dict[str, Field] = {}
    _metadata: MetaData = MetaData()

    def __init__(self, ids: Optional[List[int]] = None, env: Optional[Environment] = None):
        """
        Initialize model (returns RecordSet)

        Args:
            ids: List of record IDs
            env: Environment for this model instance
        """
        # Models are actually RecordSets
        self._ids = ids or []
        self._env = env
        self._cache = {}
        self._allow_readonly_write = False

    @classmethod
    def with_env(cls, env: Environment) -> 'Model':
        """
        Get model bound to environment

        Args:
            env: Environment to bind

        Returns:
            Model instance bound to environment
        """
        instance = cls(env=env)
        return instance

    @classmethod
    def _get_table_name(cls) -> str:
        """Get database table name"""
        if cls._table:
            return cls._table
        # Convert model name to table name (replace dots with underscores)
        return cls._name.replace('.', '_')

    @classmethod
    async def _create_table(cls, engine) -> Table:
        """
        Create SQLAlchemy table schema

        Args:
            engine: Database engine

        Returns:
            Table object
        """
        table_name = cls._get_table_name()
        columns = []
        indexes = []

        # Add columns for stored fields
        for field_name, field in cls._fields.items():
            if not field.store:
                continue

            # Skip relational fields that don't need columns
            if isinstance(field, (One2many, Many2many)):
                continue

            # Get column type
            if isinstance(field, Char):
                col_type = String(field.size)
            elif isinstance(field, Text):
                col_type = SQLText
            elif isinstance(field, IntegerField):
                col_type = Integer
            elif isinstance(field, Float):
                col_type = SQLFloat
            elif isinstance(field, Boolean):
                col_type = SQLBoolean
            elif isinstance(field, Date):
                col_type = SQLDate
            elif isinstance(field, DateTime):
                col_type = SQLDateTime
            elif isinstance(field, Binary):
                col_type = LargeBinary
            elif isinstance(field, Selection):
                col_type = String(255)
            elif isinstance(field, Many2one):
                col_type = Integer
            else:
                logger.warning(f"Unknown field type for {field_name}, using String")
                col_type = String(255)

            # Create column
            if field_name == 'id':
                column = Column('id', Integer, primary_key=True, autoincrement=True)
            else:
                nullable = not field.required
                column = Column(field_name, col_type, nullable=nullable)

            columns.append(column)

            # Add index if requested
            if field.index and field_name != 'id':
                index = Index(f'idx_{table_name}_{field_name}', field_name)
                indexes.append(index)

        # Create table
        table = Table(table_name, cls._metadata, *columns, *indexes)

        # Create table in database
        async with engine.begin() as conn:
            await conn.run_sync(cls._metadata.create_all)

        return table

    async def create(self, vals: Dict[str, Any]) -> 'RecordSet':
        """
        Create new record(s)

        Args:
            vals: Dictionary of field values or list of dictionaries

        Returns:
            RecordSet with created record(s)
        """
        if not isinstance(vals, list):
            vals = [vals]

        created_ids = []
        session: AsyncSession = self._env.session

        for values in vals:
            # Apply defaults
            record_values = {}
            for field_name, field in self._fields.items():
                if field_name in values:
                    record_values[field_name] = values[field_name]
                elif field_name != 'id' and field.store:
                    default = field.get_default(self)
                    if default is not None:
                        record_values[field_name] = default

            # Validate required fields
            for field_name, field in self._fields.items():
                if field.required and field_name != 'id':
                    if field_name not in record_values or record_values[field_name] is None:
                        raise ValueError(f"Required field '{field_name}' is missing")

            # Build INSERT query
            table_name = self._get_table_name()
            columns = [k for k in record_values.keys() if k != 'id']
            values_str = ', '.join([f':{k}' for k in columns])
            columns_str = ', '.join(columns)

            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str}) RETURNING id"

            # Execute query
            result = await session.execute(text(query), record_values)
            record_id = result.scalar()
            created_ids.append(record_id)

        await session.commit()

        # Return recordset with created records
        return RecordSet(self.__class__, created_ids, self._cache)

    async def write(self, vals: Dict[str, Any]) -> bool:
        """
        Update record(s)

        Args:
            vals: Dictionary of field values to update

        Returns:
            True if successful
        """
        if not self._ids:
            return True

        session: AsyncSession = self._env.session

        # Validate readonly fields
        for field_name in vals.keys():
            if field_name in self._fields:
                field = self._fields[field_name]
                if field.readonly and not self._allow_readonly_write:
                    raise ValueError(f"Field '{field_name}' is readonly")

        # Build UPDATE query
        table_name = self._get_table_name()
        set_parts = [f"{k} = :{k}" for k in vals.keys()]
        set_clause = ', '.join(set_parts)

        placeholders = ', '.join([':id' + str(i) for i in range(len(self._ids))])
        id_params = {f'id{i}': id_val for i, id_val in enumerate(self._ids)}

        query = f"UPDATE {table_name} SET {set_clause} WHERE id IN ({placeholders})"

        # Combine parameters
        params = {**vals, **id_params}

        # Execute query
        await session.execute(text(query), params)
        await session.commit()

        # Invalidate cache
        self._env.invalidate_cache()

        return True

    async def unlink(self) -> bool:
        """
        Delete record(s)

        Returns:
            True if successful
        """
        if not self._ids:
            return True

        session: AsyncSession = self._env.session

        # Build DELETE query
        table_name = self._get_table_name()
        placeholders = ', '.join([':id' + str(i) for i in range(len(self._ids))])
        params = {f'id{i}': id_val for i, id_val in enumerate(self._ids)}

        query = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"

        # Execute query
        await session.execute(text(query), params)
        await session.commit()

        # Clear IDs
        self._ids = []

        return True

    async def read(self, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Read field values from record(s)

        Args:
            fields: List of field names to read (None = all fields)

        Returns:
            List of dictionaries with field values
        """
        if not self._ids:
            return []

        session: AsyncSession = self._env.session

        # Determine fields to read
        if fields is None:
            fields = [name for name, field in self._fields.items() if field.store]
        else:
            # Ensure 'id' is included
            if 'id' not in fields:
                fields = ['id'] + fields

        # Build SELECT query
        table_name = self._get_table_name()
        columns = ', '.join(fields)
        placeholders = ', '.join([':id' + str(i) for i in range(len(self._ids))])
        params = {f'id{i}': id_val for i, id_val in enumerate(self._ids)}

        query = f"SELECT {columns} FROM {table_name} WHERE id IN ({placeholders})"

        # Execute query
        result = await session.execute(text(query), params)
        rows = result.fetchall()

        # Convert to list of dicts
        records = []
        for row in rows:
            record = {}
            for i, field_name in enumerate(fields):
                record[field_name] = row[i]
            records.append(record)

        return records

    async def search(
        self,
        domain: List = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> 'RecordSet':
        """
        Search for records matching domain

        Args:
            domain: Search domain (None = all records)
            offset: Number of records to skip
            limit: Maximum number of records to return
            order: Order clause (e.g., 'name ASC, id DESC')

        Returns:
            RecordSet with matching records
        """
        session: AsyncSession = self._env.session

        # Build SELECT query
        table_name = self._get_table_name()
        query = f"SELECT id FROM {table_name}"

        # Add WHERE clause
        params = {}
        if domain:
            where_clause, where_params = domain_to_sql(domain, self.__class__, table_name)
            query += f" WHERE {where_clause}"
            params.update({f'p{i}': p for i, p in enumerate(where_params)})
            # Replace %s with :pN
            for i in range(len(where_params)):
                query = query.replace('%s', f':p{i}', 1)

        # Add ORDER BY clause
        if order:
            query += f" ORDER BY {order}"
        elif self._order:
            query += f" ORDER BY {self._order}"

        # Add LIMIT and OFFSET
        if limit:
            query += f" LIMIT {limit}"
        if offset:
            query += f" OFFSET {offset}"

        # Execute query
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        ids = [row[0] for row in rows]

        return RecordSet(self.__class__, ids, self._cache)

    async def search_count(self, domain: List = None) -> int:
        """
        Count records matching domain

        Args:
            domain: Search domain (None = all records)

        Returns:
            Number of matching records
        """
        session: AsyncSession = self._env.session

        # Build COUNT query
        table_name = self._get_table_name()
        query = f"SELECT COUNT(*) FROM {table_name}"

        # Add WHERE clause
        params = {}
        if domain:
            where_clause, where_params = domain_to_sql(domain, self.__class__, table_name)
            query += f" WHERE {where_clause}"
            params.update({f'p{i}': p for i, p in enumerate(where_params)})
            # Replace %s with :pN
            for i in range(len(where_params)):
                query = query.replace('%s', f':p{i}', 1)

        # Execute query
        result = await session.execute(text(query), params)
        count = result.scalar()

        return count

    @classmethod
    def browse(cls, ids: Union[int, List[int]], env: Optional[Environment] = None) -> 'RecordSet':
        """
        Get recordset by IDs

        Args:
            ids: Single ID or list of IDs
            env: Environment to use

        Returns:
            RecordSet with specified IDs
        """
        if isinstance(ids, int):
            ids = [ids]

        instance = cls(ids=ids, env=env)
        return RecordSet(cls, ids, instance._cache)

    def _get_field_value(self, field_name: str) -> Any:
        """Get field value (used by RecordSet)"""
        if field_name not in self._fields:
            raise AttributeError(f"Model '{self._name}' has no field '{field_name}'")

        field = self._fields[field_name]

        # Check cache
        if self._ids and len(self._ids) == 1:
            cache_key = (self._ids[0], field_name)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Computed field
        if field.compute and not field.related:
            compute_method = getattr(self, field.compute)
            value = compute_method()
            if self._ids and len(self._ids) == 1:
                self._cache[(self._ids[0], field_name)] = value
            return value

        # Related field
        if field.related:
            # Traverse relationship
            parts = field.related.split('.')
            value = self
            for part in parts:
                value = getattr(value, part)
            return value

        # Regular stored field - need to fetch from DB
        # This is a placeholder - in real implementation would fetch from DB
        return None

    def _set_field_value(self, field_name: str, value: Any):
        """Set field value (used by RecordSet)"""
        if field_name not in self._fields:
            raise AttributeError(f"Model '{self._name}' has no field '{field_name}'")

        # Update cache
        if self._ids:
            for record_id in self._ids:
                cache_key = (record_id, field_name)
                self._cache[cache_key] = value

    @classmethod
    async def _get_field_value_from_db(cls, record_id: int, field_name: str) -> Any:
        """Fetch field value from database"""
        # This is a placeholder - in real implementation would fetch from DB
        return None

    def __getattr__(self, name):
        """Get field value or method"""
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        if name in self._fields:
            return self._get_field_value(name)

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Set field value"""
        # Allow setting internal attributes
        if name.startswith('_') or name in ['_ids', '_env', '_cache', '_allow_readonly_write']:
            super().__setattr__(name, value)
            return

        # Set field value
        if hasattr(self.__class__, '_fields') and name in self._fields:
            self._set_field_value(name, value)
        else:
            super().__setattr__(name, value)
