"""
Domain expression parser for search queries

Domains are lists representing search criteria in Polish notation.
Examples:
    [('name', '=', 'John')]
    ['&', ('age', '>', 18), ('active', '=', True)]
    ['|', ('state', '=', 'draft'), ('state', '=', 'open')]
"""
from typing import List, Tuple, Any, Union, Optional
from enum import Enum


class DomainOperator(str, Enum):
    """Domain operators for comparisons"""
    EQ = '='
    NE = '!='
    GT = '>'
    LT = '<'
    GTE = '>='
    LTE = '<='
    LIKE = 'like'
    ILIKE = 'ilike'
    IN = 'in'
    NOT_IN = 'not in'
    CHILD_OF = 'child_of'
    PARENT_OF = 'parent_of'


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions"""
    AND = '&'
    OR = '|'
    NOT = '!'


# Type alias for domain expressions
DomainLeaf = Tuple[str, str, Any]
Domain = List[Union[str, DomainLeaf]]


class DomainParser:
    """
    Parser for domain expressions

    Domains use Polish (prefix) notation for logical operators:
    - ['&', condition1, condition2] = condition1 AND condition2
    - ['|', condition1, condition2] = condition1 OR condition2
    - ['!', condition] = NOT condition

    Conditions are tuples: (field_name, operator, value)
    """

    def __init__(self, domain: Optional[Domain] = None):
        """
        Initialize domain parser

        Args:
            domain: Domain expression to parse
        """
        self.domain = domain or []
        self.position = 0

    def normalize(self) -> Domain:
        """
        Normalize domain to standard form

        Adds implicit AND operators and validates structure

        Returns:
            Normalized domain
        """
        if not self.domain:
            return []

        # Count logical operators vs conditions
        op_count = sum(1 for item in self.domain if isinstance(item, str) and item in ['&', '|', '!'])
        leaf_count = sum(1 for item in self.domain if isinstance(item, tuple))

        # If no operators, add implicit ANDs
        if op_count == 0 and leaf_count > 1:
            # Add AND operators between all conditions
            result = []
            for i in range(leaf_count - 1):
                result.append('&')
            result.extend(self.domain)
            return result

        return self.domain

    def parse(self) -> 'DomainNode':
        """
        Parse domain into AST

        Returns:
            Root node of domain AST
        """
        normalized = self.normalize()
        if not normalized:
            return DomainNode('&', [])  # Empty domain matches everything

        self.domain = normalized
        self.position = 0
        return self._parse_expression()

    def _parse_expression(self) -> 'DomainNode':
        """Parse a single domain expression"""
        if self.position >= len(self.domain):
            raise ValueError("Unexpected end of domain")

        current = self.domain[self.position]
        self.position += 1

        # Logical operators
        if isinstance(current, str):
            if current == '!':
                # NOT operator - requires 1 operand
                operand = self._parse_expression()
                return DomainNode('!', [operand])
            elif current in ['&', '|']:
                # AND/OR operators - require 2 operands
                left = self._parse_expression()
                right = self._parse_expression()
                return DomainNode(current, [left, right])
            else:
                raise ValueError(f"Unknown operator: {current}")

        # Leaf condition
        elif isinstance(current, (tuple, list)):
            if len(current) != 3:
                raise ValueError(f"Invalid domain leaf: {current}")
            field, operator, value = current
            return DomainNode('leaf', [], field=field, operator=operator, value=value)

        else:
            raise ValueError(f"Invalid domain element: {current}")

    def to_sql(self, model_class, alias: str = 'main') -> Tuple[str, List[Any]]:
        """
        Convert domain to SQL WHERE clause

        Args:
            model_class: Model class for field lookups
            alias: Table alias to use

        Returns:
            Tuple of (sql_string, parameters)
        """
        if not self.domain:
            return ('TRUE', [])

        ast = self.parse()
        return ast.to_sql(model_class, alias)


class DomainNode:
    """
    Node in domain AST

    Each node represents either:
    - A logical operator (AND, OR, NOT) with child nodes
    - A leaf condition (field, operator, value)
    """

    def __init__(
        self,
        operator: str,
        children: List['DomainNode'],
        field: Optional[str] = None,
        comparison_op: Optional[str] = None,
        value: Any = None
    ):
        """
        Initialize domain node

        Args:
            operator: Logical operator ('&', '|', '!', 'leaf')
            children: Child nodes
            field: Field name (for leaf nodes)
            comparison_op: Comparison operator (for leaf nodes)
            value: Comparison value (for leaf nodes)
        """
        self.operator = operator
        self.children = children
        self.field = field
        self.comparison_op = comparison_op
        self.value = value

    def to_sql(self, model_class, alias: str = 'main') -> Tuple[str, List[Any]]:
        """
        Convert node to SQL

        Args:
            model_class: Model class for field lookups
            alias: Table alias

        Returns:
            Tuple of (sql_string, parameters)
        """
        if self.operator == 'leaf':
            return self._leaf_to_sql(model_class, alias)
        elif self.operator == '&':
            return self._and_to_sql(model_class, alias)
        elif self.operator == '|':
            return self._or_to_sql(model_class, alias)
        elif self.operator == '!':
            return self._not_to_sql(model_class, alias)
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    def _leaf_to_sql(self, model_class, alias: str) -> Tuple[str, List[Any]]:
        """Convert leaf condition to SQL"""
        field_name = self.field
        operator = self.comparison_op
        value = self.value

        # Get field from model
        if not hasattr(model_class, field_name):
            raise ValueError(f"Field '{field_name}' not found on model '{model_class._name}'")

        # Handle special case for id field
        if field_name == 'id':
            column = f"{alias}.id"
        else:
            column = f"{alias}.{field_name}"

        # Convert operator to SQL
        if operator == '=':
            if value is None or value is False:
                return (f"{column} IS NULL", [])
            return (f"{column} = %s", [value])

        elif operator == '!=':
            if value is None or value is False:
                return (f"{column} IS NOT NULL", [])
            return (f"{column} != %s", [value])

        elif operator == '>':
            return (f"{column} > %s", [value])

        elif operator == '<':
            return (f"{column} < %s", [value])

        elif operator == '>=':
            return (f"{column} >= %s", [value])

        elif operator == '<=':
            return (f"{column} <= %s", [value])

        elif operator == 'like':
            return (f"{column} LIKE %s", [value])

        elif operator == 'ilike':
            return (f"{column} ILIKE %s", [value])

        elif operator == 'in':
            if not value:
                return ('FALSE', [])
            placeholders = ', '.join(['%s'] * len(value))
            return (f"{column} IN ({placeholders})", list(value))

        elif operator == 'not in':
            if not value:
                return ('TRUE', [])
            placeholders = ', '.join(['%s'] * len(value))
            return (f"{column} NOT IN ({placeholders})", list(value))

        elif operator in ['child_of', 'parent_of']:
            # These require hierarchical query support
            raise NotImplementedError(f"Operator '{operator}' not yet implemented")

        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _and_to_sql(self, model_class, alias: str) -> Tuple[str, List[Any]]:
        """Convert AND node to SQL"""
        if not self.children:
            return ('TRUE', [])

        parts = []
        params = []
        for child in self.children:
            sql, child_params = child.to_sql(model_class, alias)
            parts.append(f"({sql})")
            params.extend(child_params)

        return (' AND '.join(parts), params)

    def _or_to_sql(self, model_class, alias: str) -> Tuple[str, List[Any]]:
        """Convert OR node to SQL"""
        if not self.children:
            return ('FALSE', [])

        parts = []
        params = []
        for child in self.children:
            sql, child_params = child.to_sql(model_class, alias)
            parts.append(f"({sql})")
            params.extend(child_params)

        return (' OR '.join(parts), params)

    def _not_to_sql(self, model_class, alias: str) -> Tuple[str, List[Any]]:
        """Convert NOT node to SQL"""
        if not self.children:
            return ('TRUE', [])

        sql, params = self.children[0].to_sql(model_class, alias)
        return (f"NOT ({sql})", params)

    def __repr__(self) -> str:
        """String representation of node"""
        if self.operator == 'leaf':
            return f"Leaf({self.field} {self.comparison_op} {self.value})"
        else:
            return f"{self.operator}({', '.join(map(str, self.children))})"


def normalize_domain(domain: Domain) -> Domain:
    """
    Normalize domain expression

    Args:
        domain: Domain to normalize

    Returns:
        Normalized domain
    """
    parser = DomainParser(domain)
    return parser.normalize()


def domain_to_sql(domain: Domain, model_class, alias: str = 'main') -> Tuple[str, List[Any]]:
    """
    Convert domain to SQL WHERE clause

    Args:
        domain: Domain expression
        model_class: Model class for field lookups
        alias: Table alias

    Returns:
        Tuple of (sql_string, parameters)
    """
    parser = DomainParser(domain)
    return parser.to_sql(model_class, alias)
