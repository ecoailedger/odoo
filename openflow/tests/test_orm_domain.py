"""
Tests for ORM domain expression parser
"""
import pytest

from openflow.server.core.orm import (
    Model, fields, DomainParser, normalize_domain, domain_to_sql
)


# Mock model for testing
class TestModel(Model):
    _name = 'test.model'
    _table = 'test_model'

    name = fields.Char(string='Name')
    age = fields.Integer(string='Age')
    active = fields.Boolean(string='Active')
    email = fields.Char(string='Email')


class TestDomainNormalization:
    """Test domain normalization"""

    def test_empty_domain(self):
        """Test empty domain"""
        parser = DomainParser([])
        assert parser.normalize() == []

    def test_single_condition(self):
        """Test single condition (no normalization needed)"""
        domain = [('name', '=', 'John')]
        parser = DomainParser(domain)
        assert parser.normalize() == domain

    def test_implicit_and(self):
        """Test implicit AND between multiple conditions"""
        domain = [('name', '=', 'John'), ('age', '>', 18)]
        parser = DomainParser(domain)
        normalized = parser.normalize()

        # Should add & operator
        assert normalized[0] == '&'
        assert normalized[1] == ('name', '=', 'John')
        assert normalized[2] == ('age', '>', 18)

    def test_implicit_and_three_conditions(self):
        """Test implicit AND with three conditions"""
        domain = [
            ('name', '=', 'John'),
            ('age', '>', 18),
            ('active', '=', True)
        ]
        parser = DomainParser(domain)
        normalized = parser.normalize()

        # Should add two & operators
        assert normalized[0] == '&'
        assert normalized[1] == '&'
        assert len(normalized) == 5  # 2 ANDs + 3 conditions

    def test_explicit_operators(self):
        """Test domain with explicit operators (no change)"""
        domain = ['&', ('name', '=', 'John'), ('age', '>', 18)]
        parser = DomainParser(domain)
        assert parser.normalize() == domain


class TestDomainParsing:
    """Test domain parsing to AST"""

    def test_parse_single_condition(self):
        """Test parsing single condition"""
        domain = [('name', '=', 'John')]
        parser = DomainParser(domain)
        ast = parser.parse()

        # Implicit AND with single condition
        assert ast.operator == '&'

    def test_parse_and_operator(self):
        """Test parsing AND operator"""
        domain = ['&', ('name', '=', 'John'), ('age', '>', 18)]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '&'
        assert len(ast.children) == 2
        assert ast.children[0].field == 'name'
        assert ast.children[1].field == 'age'

    def test_parse_or_operator(self):
        """Test parsing OR operator"""
        domain = ['|', ('state', '=', 'draft'), ('state', '=', 'open')]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '|'
        assert len(ast.children) == 2
        assert ast.children[0].comparison_op == '='
        assert ast.children[1].comparison_op == '='

    def test_parse_not_operator(self):
        """Test parsing NOT operator"""
        domain = ['!', ('active', '=', False)]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '!'
        assert len(ast.children) == 1
        assert ast.children[0].field == 'active'

    def test_parse_nested_operators(self):
        """Test parsing nested operators"""
        domain = [
            '&',
            ('active', '=', True),
            '|',
            ('state', '=', 'draft'),
            ('state', '=', 'open')
        ]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '&'
        assert len(ast.children) == 2
        assert ast.children[0].field == 'active'
        assert ast.children[1].operator == '|'

    def test_parse_complex_domain(self):
        """Test parsing complex domain"""
        domain = [
            '&',
            '&',
            ('active', '=', True),
            ('age', '>', 18),
            '|',
            ('state', '=', 'draft'),
            ('state', '=', 'open')
        ]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '&'
        assert ast.children[0].operator == '&'
        assert ast.children[1].operator == '|'


class TestDomainToSQL:
    """Test domain to SQL conversion"""

    def test_simple_equality(self):
        """Test simple equality"""
        domain = [('name', '=', 'John')]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'name = %s' in sql
        assert 'John' in params

    def test_inequality(self):
        """Test inequality operator"""
        domain = [('age', '!=', 18)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'age != %s' in sql
        assert 18 in params

    def test_greater_than(self):
        """Test greater than"""
        domain = [('age', '>', 18)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'age > %s' in sql
        assert 18 in params

    def test_less_than(self):
        """Test less than"""
        domain = [('age', '<', 65)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'age < %s' in sql
        assert 65 in params

    def test_greater_equal(self):
        """Test greater than or equal"""
        domain = [('age', '>=', 18)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'age >= %s' in sql
        assert 18 in params

    def test_less_equal(self):
        """Test less than or equal"""
        domain = [('age', '<=', 65)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'age <= %s' in sql
        assert 65 in params

    def test_like_operator(self):
        """Test LIKE operator"""
        domain = [('name', 'like', 'John%')]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'LIKE' in sql
        assert 'John%' in params

    def test_ilike_operator(self):
        """Test ILIKE operator (case-insensitive)"""
        domain = [('name', 'ilike', '%john%')]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'ILIKE' in sql
        assert '%john%' in params

    def test_in_operator(self):
        """Test IN operator"""
        domain = [('age', 'in', [18, 25, 30])]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'IN' in sql
        assert 18 in params
        assert 25 in params
        assert 30 in params

    def test_in_operator_empty(self):
        """Test IN operator with empty list"""
        domain = [('age', 'in', [])]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'FALSE' in sql
        assert params == []

    def test_not_in_operator(self):
        """Test NOT IN operator"""
        domain = [('age', 'not in', [10, 20, 30])]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'NOT IN' in sql
        assert 10 in params

    def test_not_in_operator_empty(self):
        """Test NOT IN operator with empty list"""
        domain = [('age', 'not in', [])]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'TRUE' in sql
        assert params == []

    def test_null_value_equality(self):
        """Test NULL value with = operator"""
        domain = [('name', '=', None)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'IS NULL' in sql
        assert params == []

    def test_null_value_inequality(self):
        """Test NULL value with != operator"""
        domain = [('name', '!=', None)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'IS NOT NULL' in sql
        assert params == []

    def test_false_value_equality(self):
        """Test False value with = operator"""
        domain = [('active', '=', False)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'IS NULL' in sql
        assert params == []


class TestDomainLogicalOperators:
    """Test logical operators in SQL generation"""

    def test_and_operator(self):
        """Test AND operator"""
        domain = ['&', ('name', '=', 'John'), ('age', '>', 18)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'AND' in sql
        assert 'name = %s' in sql
        assert 'age > %s' in sql
        assert 'John' in params
        assert 18 in params

    def test_or_operator(self):
        """Test OR operator"""
        domain = ['|', ('state', '=', 'draft'), ('state', '=', 'open')]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'OR' in sql
        assert sql.count('state') >= 2  # Should appear twice

    def test_not_operator(self):
        """Test NOT operator"""
        domain = ['!', ('active', '=', False)]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'NOT' in sql
        assert 'active' in sql

    def test_complex_logic(self):
        """Test complex logical combination"""
        domain = [
            '&',
            ('active', '=', True),
            '|',
            ('name', 'like', 'John%'),
            ('email', 'like', '%@example.com')
        ]
        parser = DomainParser(domain)
        sql, params = parser.to_sql(TestModel, 'test_model')

        assert 'AND' in sql
        assert 'OR' in sql
        assert 'active' in sql
        assert 'name' in sql
        assert 'email' in sql


class TestDomainHelperFunctions:
    """Test helper functions"""

    def test_normalize_domain_function(self):
        """Test normalize_domain helper"""
        domain = [('name', '=', 'John'), ('age', '>', 18)]
        normalized = normalize_domain(domain)

        assert normalized[0] == '&'
        assert len(normalized) == 3

    def test_domain_to_sql_function(self):
        """Test domain_to_sql helper"""
        domain = [('name', '=', 'John')]
        sql, params = domain_to_sql(domain, TestModel)

        assert 'name' in sql
        assert 'John' in params

    def test_empty_domain(self):
        """Test empty domain returns TRUE"""
        sql, params = domain_to_sql([], TestModel)
        assert 'TRUE' in sql or sql == ''


class TestDomainErrors:
    """Test domain error handling"""

    def test_invalid_field(self):
        """Test error for invalid field"""
        domain = [('nonexistent_field', '=', 'value')]
        parser = DomainParser(domain)

        with pytest.raises(ValueError, match="not found"):
            parser.to_sql(TestModel, 'test_model')

    def test_invalid_operator(self):
        """Test error for invalid operator"""
        domain = [('name', 'invalid_op', 'value')]
        parser = DomainParser(domain)

        with pytest.raises(ValueError, match="Unknown operator"):
            parser.to_sql(TestModel, 'test_model')

    def test_malformed_leaf(self):
        """Test error for malformed leaf"""
        domain = [('name', '=')]  # Missing value
        parser = DomainParser(domain)

        with pytest.raises(ValueError, match="Invalid domain leaf"):
            parser.parse()

    def test_unknown_logical_operator(self):
        """Test error for unknown logical operator"""
        domain = ['%', ('name', '=', 'John')]
        parser = DomainParser(domain)

        with pytest.raises(ValueError, match="Unknown operator"):
            parser.parse()


class TestDomainEdgeCases:
    """Test edge cases"""

    def test_nested_not_operators(self):
        """Test nested NOT operators"""
        domain = ['!', '!', ('active', '=', True)]
        parser = DomainParser(domain)
        ast = parser.parse()

        assert ast.operator == '!'
        assert ast.children[0].operator == '!'

    def test_deeply_nested_logic(self):
        """Test deeply nested logical operators"""
        domain = [
            '&',
            '&',
            ('a', '=', 1),
            '|',
            ('b', '=', 2),
            ('c', '=', 3),
            '!',
            ('d', '=', 4)
        ]
        parser = DomainParser(domain)
        ast = parser.parse()

        # Should parse without errors
        assert ast.operator == '&'

    def test_multiple_implicit_ands(self):
        """Test multiple conditions with implicit ANDs"""
        domain = [
            ('a', '=', 1),
            ('b', '=', 2),
            ('c', '=', 3),
            ('d', '=', 4)
        ]
        parser = DomainParser(domain)
        normalized = parser.normalize()

        # Should add 3 AND operators
        and_count = sum(1 for item in normalized if item == '&')
        assert and_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
