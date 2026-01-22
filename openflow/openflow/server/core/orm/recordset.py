"""
Recordset class for handling collections of model records

Recordsets represent collections of records from the same model and provide
methods to manipulate them collectively.
"""
from typing import Any, Dict, List, Optional, Iterator, Union


class RecordSet:
    """
    Collection of records from the same model

    RecordSets are immutable and all operations return new RecordSets.
    They support iteration, indexing, and various set operations.
    """

    def __init__(self, model, ids: Optional[List[int]] = None, cache: Optional[Dict] = None):
        """
        Initialize a RecordSet

        Args:
            model: The model class this recordset belongs to
            ids: List of record IDs in this recordset
            cache: Optional cache dictionary for field values
        """
        self._model = model
        self._ids = list(ids) if ids else []
        self._cache = cache or {}
        self._allow_readonly_write = False

    def __len__(self) -> int:
        """Return number of records in recordset"""
        return len(self._ids)

    def __bool__(self) -> bool:
        """RecordSet is truthy if it contains records"""
        return bool(self._ids)

    def __iter__(self) -> Iterator['RecordSet']:
        """Iterate over individual records as singleton recordsets"""
        for record_id in self._ids:
            yield RecordSet(self._model, [record_id], self._cache)

    def __getitem__(self, index: Union[int, slice]) -> 'RecordSet':
        """Get record(s) by index"""
        if isinstance(index, slice):
            return RecordSet(self._model, self._ids[index], self._cache)
        else:
            return RecordSet(self._model, [self._ids[index]], self._cache)

    def __eq__(self, other) -> bool:
        """Check if two recordsets are equal (same model and IDs)"""
        if not isinstance(other, RecordSet):
            return False
        return (self._model == other._model and
                set(self._ids) == set(other._ids))

    def __add__(self, other: 'RecordSet') -> 'RecordSet':
        """Union of two recordsets (no duplicates)"""
        if not isinstance(other, RecordSet) or self._model != other._model:
            raise ValueError("Can only add recordsets from the same model")
        # Preserve order, no duplicates
        new_ids = self._ids.copy()
        for record_id in other._ids:
            if record_id not in new_ids:
                new_ids.append(record_id)
        return RecordSet(self._model, new_ids, {**self._cache, **other._cache})

    def __sub__(self, other: 'RecordSet') -> 'RecordSet':
        """Difference of two recordsets"""
        if not isinstance(other, RecordSet) or self._model != other._model:
            raise ValueError("Can only subtract recordsets from the same model")
        new_ids = [rid for rid in self._ids if rid not in other._ids]
        return RecordSet(self._model, new_ids, self._cache)

    def __and__(self, other: 'RecordSet') -> 'RecordSet':
        """Intersection of two recordsets"""
        if not isinstance(other, RecordSet) or self._model != other._model:
            raise ValueError("Can only intersect recordsets from the same model")
        other_ids = set(other._ids)
        new_ids = [rid for rid in self._ids if rid in other_ids]
        return RecordSet(self._model, new_ids, {**self._cache, **other._cache})

    def __or__(self, other: 'RecordSet') -> 'RecordSet':
        """Union of two recordsets (alias for +)"""
        return self + other

    def __repr__(self) -> str:
        """String representation of recordset"""
        return f"{self._model._name}({', '.join(map(str, self._ids))})"

    @property
    def ids(self) -> List[int]:
        """Get list of IDs in this recordset"""
        return self._ids.copy()

    @property
    def id(self) -> Optional[int]:
        """Get ID of singleton recordset, None for empty, raise for multi"""
        if not self._ids:
            return None
        if len(self._ids) > 1:
            raise ValueError("Expected singleton recordset")
        return self._ids[0]

    def ensure_one(self) -> 'RecordSet':
        """Ensure recordset contains exactly one record"""
        if len(self._ids) != 1:
            raise ValueError(f"Expected singleton recordset, got {len(self._ids)} records")
        return self

    def exists(self) -> 'RecordSet':
        """
        Filter recordset to only existing records

        Returns a new recordset containing only records that exist in database
        """
        # This will be implemented when we have database access
        # For now, return self
        return self

    def filtered(self, func) -> 'RecordSet':
        """
        Filter recordset based on predicate function

        Args:
            func: Function that takes a record and returns boolean, or string domain

        Returns:
            New recordset with records matching the predicate
        """
        if isinstance(func, str):
            # Domain string - will be implemented with domain parser
            raise NotImplementedError("Domain string filtering not yet implemented")

        filtered_ids = []
        for record in self:
            if func(record):
                filtered_ids.append(record.id)

        return RecordSet(self._model, filtered_ids, self._cache)

    def sorted(self, key=None, reverse=False) -> 'RecordSet':
        """
        Sort recordset based on key function

        Args:
            key: Function to extract comparison key from record
            reverse: Whether to sort in reverse order

        Returns:
            New sorted recordset
        """
        if key is None:
            key = lambda r: r.id

        sorted_records = sorted(self, key=key, reverse=reverse)
        sorted_ids = [r.id for r in sorted_records]
        return RecordSet(self._model, sorted_ids, self._cache)

    def mapped(self, field_name: str) -> List[Any]:
        """
        Map recordset to list of field values

        Args:
            field_name: Name of field to extract

        Returns:
            List of field values (may contain duplicates)
        """
        result = []
        for record in self:
            value = getattr(record, field_name)
            if isinstance(value, RecordSet):
                result.extend(value)
            else:
                result.append(value)
        return result

    def _get_field_value(self, field_name: str) -> Any:
        """
        Get field value for recordset

        For singleton recordsets, returns the field value.
        For multi-record recordsets, returns list of values.
        """
        if not self._ids:
            return None

        # Check cache first
        cache_key = (self._ids[0], field_name)
        if cache_key in self._cache:
            if len(self._ids) == 1:
                return self._cache[cache_key]

        # For singleton, get value from model
        if len(self._ids) == 1:
            return self._model._get_field_value_from_db(self._ids[0], field_name)

        # For multi-record, return list of values
        return [getattr(RecordSet(self._model, [rid], self._cache), field_name)
                for rid in self._ids]

    def _set_field_value(self, field_name: str, value: Any):
        """Set field value for recordset"""
        if not self._ids:
            raise ValueError("Cannot set value on empty recordset")

        # For singleton, update cache
        if len(self._ids) == 1:
            cache_key = (self._ids[0], field_name)
            self._cache[cache_key] = value
        else:
            # For multi-record, set same value on all records
            for record_id in self._ids:
                cache_key = (record_id, field_name)
                self._cache[cache_key] = value

    def write(self, values: Dict[str, Any]) -> bool:
        """
        Update records with values

        Args:
            values: Dictionary of field names to values

        Returns:
            True if successful
        """
        return self._model.write(self._ids, values)

    def unlink(self) -> bool:
        """
        Delete records

        Returns:
            True if successful
        """
        return self._model.unlink(self._ids)

    def read(self, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Read field values

        Args:
            fields: List of field names to read (None = all fields)

        Returns:
            List of dictionaries containing field values
        """
        return self._model.read(self._ids, fields)

    def copy(self, default: Optional[Dict[str, Any]] = None) -> 'RecordSet':
        """
        Duplicate record(s)

        Args:
            default: Dictionary of field values to override in copy

        Returns:
            New recordset with copied records
        """
        if len(self._ids) != 1:
            raise ValueError("Can only copy singleton recordset")
        new_id = self._model.copy(self._ids[0], default)
        return RecordSet(self._model, [new_id])
