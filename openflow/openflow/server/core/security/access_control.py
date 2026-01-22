"""Access control enforcement for models and records.

This module provides the core logic for checking permissions based on:
1. Model-level access (ir.model.access) - CRUD permissions
2. Record-level access (ir.rule) - Domain-based filtering
3. Field-level access - Group-based field visibility
4. Multi-company access - Company-based filtering
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any, Literal
from .exceptions import AccessDenied, InsufficientPermissions

if TYPE_CHECKING:
    from openflow.server.core.orm.registry import Environment

# Superuser ID that bypasses all access checks
SUPERUSER_ID = 1


OperationType = Literal["read", "write", "create", "unlink"]


class AccessController:
    """Handles access control checks for models and records."""

    def __init__(self, env: "Environment"):
        """Initialize access controller with environment.

        Args:
            env: The environment containing user and database context
        """
        self.env = env
        self.user = env.user
        self.context = env.context

    def is_superuser(self) -> bool:
        """Check if the current user is a superuser.

        Superusers bypass all access checks.

        Returns:
            True if user is superuser
        """
        if not self.user:
            return False
        return getattr(self.user, 'id', None) == SUPERUSER_ID

    def check_model_access(
        self,
        model_name: str,
        operation: OperationType,
        raise_exception: bool = True
    ) -> bool:
        """Check if user has model-level access for an operation.

        This checks ir.model.access records to verify if the user's groups
        have permission to perform the operation on the model.

        Args:
            model_name: Name of the model (e.g., 'res.users')
            operation: The operation to check ('read', 'write', 'create', 'unlink')
            raise_exception: Whether to raise exception on denied access

        Returns:
            True if access is granted

        Raises:
            AccessDenied: If access is denied and raise_exception is True

        Example:
            >>> controller.check_model_access('res.partner', 'read')
            True
            >>> controller.check_model_access('res.users', 'unlink')
            False  # or raises AccessDenied
        """
        # Superuser bypasses all checks
        if self.is_superuser():
            return True

        # If no user, deny access
        if not self.user:
            if raise_exception:
                raise AccessDenied(
                    f"Access denied: No user context for {operation} on {model_name}"
                )
            return False

        # Get user's groups
        user_groups = self._get_user_groups()

        # Query ir.model.access for matching rules
        has_access = self._check_access_rules(
            model_name,
            operation,
            user_groups
        )

        if not has_access and raise_exception:
            raise InsufficientPermissions(
                f"Access denied: User lacks {operation} permission on {model_name}"
            )

        return has_access

    def _get_user_groups(self) -> List[int]:
        """Get list of group IDs for the current user.

        Returns:
            List of group IDs
        """
        if not self.user:
            return []

        # Get groups from user
        groups = getattr(self.user, 'groups_id', None)
        if groups:
            # Handle RecordSet or list
            if hasattr(groups, 'ids'):
                return groups.ids
            return list(groups)

        return []

    def _check_access_rules(
        self,
        model_name: str,
        operation: OperationType,
        user_groups: List[int]
    ) -> bool:
        """Check ir.model.access rules for permission.

        Args:
            model_name: Model name
            operation: Operation type
            user_groups: User's group IDs

        Returns:
            True if access is granted
        """
        # Map operation to permission field
        perm_field = f"perm_{operation}"

        # In a real implementation, this would query ir.model.access
        # For now, we'll assume access is granted if user has groups
        # This will be implemented properly when we integrate with ORM

        # TODO: Implement actual query to ir.model.access
        # SELECT * FROM ir_model_access
        # WHERE model_id = (SELECT id FROM ir_model WHERE model = model_name)
        # AND (group_id IS NULL OR group_id IN user_groups)
        # AND perm_field = TRUE

        # For now, allow access if user is authenticated
        return len(user_groups) > 0 or self.user is not None

    def get_record_rules(
        self,
        model_name: str,
        operation: OperationType
    ) -> List[Dict[str, Any]]:
        """Get applicable record rules for a model and operation.

        Record rules (ir.rule) provide row-level security by filtering
        records based on domain expressions.

        Args:
            model_name: Model name
            operation: Operation type

        Returns:
            List of rule dictionaries with 'domain_force' and 'groups'

        Example:
            >>> rules = controller.get_record_rules('res.partner', 'read')
            >>> # Returns: [{'domain_force': [('user_id', '=', user.id)], ...}]
        """
        # Superuser bypasses rules
        if self.is_superuser():
            return []

        # Get user's groups
        user_groups = self._get_user_groups()

        # TODO: Query ir.rule for applicable rules
        # Rules apply if:
        # 1. Rule applies to the operation (perm_read, perm_write, etc.)
        # 2. Rule has no groups (global) OR user is in one of the rule's groups

        # For now, return empty list (no restrictions)
        return []

    def apply_record_rules(
        self,
        model_name: str,
        operation: OperationType,
        domain: Optional[List] = None
    ) -> List:
        """Apply record rules to a domain.

        This combines the user's domain with applicable record rules
        to enforce row-level security.

        Args:
            model_name: Model name
            operation: Operation type
            domain: Base domain to filter (or None)

        Returns:
            Combined domain with record rules applied

        Example:
            >>> # User searches for partners
            >>> domain = [('active', '=', True)]
            >>> # Apply rules that restrict to user's own records
            >>> filtered = controller.apply_record_rules(
            ...     'res.partner', 'read', domain
            ... )
            >>> # Result: ['&', ('active', '=', True), ('user_id', '=', user.id)]
        """
        # Superuser bypasses rules
        if self.is_superuser():
            return domain or []

        rules = self.get_record_rules(model_name, operation)
        if not rules:
            return domain or []

        # Combine domain with rule domains using AND logic
        combined = list(domain) if domain else []

        for rule in rules:
            rule_domain = rule.get('domain_force', [])
            if rule_domain:
                if combined:
                    # AND the rule domain with existing domain
                    combined = ['&'] + combined + rule_domain
                else:
                    combined = rule_domain

        return combined

    def filter_fields(
        self,
        model_name: str,
        field_names: List[str]
    ) -> List[str]:
        """Filter fields based on user's access rights.

        Some fields may be restricted to specific groups. This method
        filters out fields the user cannot access.

        Args:
            model_name: Model name
            field_names: List of field names to filter

        Returns:
            List of accessible field names

        Example:
            >>> fields = ['name', 'email', 'password', 'salary']
            >>> accessible = controller.filter_fields('res.users', fields)
            >>> # Returns: ['name', 'email'] (password and salary hidden)
        """
        # Superuser sees all fields
        if self.is_superuser():
            return field_names

        # Get model class from registry
        from openflow.server.core.orm.registry import registry
        model_class = registry.get(model_name)
        if not model_class:
            return field_names

        # Filter fields based on groups attribute
        accessible_fields = []
        for field_name in field_names:
            if self.check_field_access(model_name, field_name):
                accessible_fields.append(field_name)

        return accessible_fields

    def check_field_access(
        self,
        model_name: str,
        field_name: str,
        operation: OperationType = "read"
    ) -> bool:
        """Check if user can access a specific field.

        Args:
            model_name: Model name
            field_name: Field name
            operation: Operation type

        Returns:
            True if user can access the field
        """
        # Superuser can access all fields
        if self.is_superuser():
            return True

        # Get model class from registry
        from openflow.server.core.orm.registry import registry
        model_class = registry.get(model_name)
        if not model_class:
            return True

        # Get field definition
        if not hasattr(model_class, '_fields'):
            return True

        field = model_class._fields.get(field_name)
        if not field:
            return True

        # Check if field has groups restriction
        if not hasattr(field, 'groups') or not field.groups:
            # No groups restriction, allow access
            return True

        # Field has groups restriction, check if user is in one of them
        if not self.user:
            return False

        # Parse groups (comma-separated external IDs)
        required_groups = [g.strip() for g in field.groups.split(',')]

        # Check if user has at least one of the required groups
        for group_ext_id in required_groups:
            if self.user.has_group(group_ext_id):
                return True

        # User is not in any of the required groups
        return False

    def get_allowed_companies(self) -> List[int]:
        """Get list of company IDs the user can access.

        This is used for multi-company security to filter records
        by company_id.

        Returns:
            List of allowed company IDs

        Example:
            >>> companies = controller.get_allowed_companies()
            >>> # Returns: [1, 3, 5] (user's allowed companies)
        """
        # Superuser can access all companies
        if self.is_superuser():
            # TODO: Return all company IDs
            return []

        if not self.user:
            return []

        # Get allowed companies from user
        company_ids = getattr(self.user, 'company_ids', None)
        if company_ids:
            if hasattr(company_ids, 'ids'):
                return company_ids.ids
            return list(company_ids)

        # Fallback to user's main company
        company_id = getattr(self.user, 'company_id', None)
        if company_id:
            if hasattr(company_id, 'id'):
                return [company_id.id]
            return [company_id]

        return []

    def apply_company_filter(
        self,
        domain: Optional[List] = None
    ) -> List:
        """Apply company filtering to a domain.

        If the model has a 'company_id' field, restrict records to
        the user's allowed companies.

        Args:
            domain: Base domain

        Returns:
            Domain with company filter applied

        Example:
            >>> domain = [('active', '=', True)]
            >>> filtered = controller.apply_company_filter(domain)
            >>> # Returns: ['&', ('active', '=', True),
            >>> #           ('company_id', 'in', [1, 3])]
        """
        # Superuser bypasses company filtering
        if self.is_superuser():
            return domain or []

        allowed_companies = self.get_allowed_companies()
        if not allowed_companies:
            return domain or []

        # Add company filter
        company_filter = [('company_id', 'in', allowed_companies)]

        if domain:
            return ['&'] + list(domain) + company_filter
        return company_filter
