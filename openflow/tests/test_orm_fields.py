"""
Tests for ORM field descriptors
"""
import pytest
from datetime import date, datetime

from openflow.server.core.orm import fields, Model


class TestFieldBasics:
    """Test basic field functionality"""

    def test_field_creation(self):
        """Test creating basic fields"""
        f = fields.Char(string='Name', required=True)
        assert f.string == 'Name'
        assert f.required is True
        assert f.readonly is False

    def test_field_default_static(self):
        """Test static default values"""
        f = fields.Boolean(default=True)
        assert f.get_default(None) is True

        f2 = fields.Integer(default=42)
        assert f2.get_default(None) == 42

    def test_field_default_callable(self):
        """Test callable default values"""
        def get_default(model):
            return 'computed'

        f = fields.Char(default=get_default)
        assert f.get_default(None) == 'computed'

    def test_field_type_defaults(self):
        """Test default values for different types"""
        assert fields.Char().get_type_default() == ''
        assert fields.Text().get_type_default() == ''
        assert fields.Integer().get_type_default() == 0
        assert fields.Float().get_type_default() == 0.0
        assert fields.Boolean().get_type_default() is False


class TestCharField:
    """Test Char field"""

    def test_char_field(self):
        """Test Char field creation"""
        f = fields.Char(string='Name', size=100, required=True)
        assert f.string == 'Name'
        assert f.size == 100
        assert f.required is True

    def test_char_field_default_size(self):
        """Test Char field default size"""
        f = fields.Char()
        assert f.size == 255

    def test_char_validation(self):
        """Test Char field validation"""
        f = fields.Char(size=10, required=True)
        f.name = 'test_field'

        # Test required validation
        with pytest.raises(ValueError, match="required"):
            f.validate(None)

        # Test size validation
        with pytest.raises(ValueError, match="exceeds maximum size"):
            f.validate('x' * 11)

        # Valid value
        assert f.validate('hello') is True


class TestTextField:
    """Test Text field"""

    def test_text_field(self):
        """Test Text field creation"""
        f = fields.Text(string='Description', translate=True)
        assert f.string == 'Description'
        assert f.translate is True


class TestNumericFields:
    """Test numeric fields"""

    def test_integer_field(self):
        """Test Integer field"""
        f = fields.Integer(string='Age', default=0)
        assert f.get_default(None) == 0
        assert f.convert_to_cache(42) == 42
        assert f.convert_to_cache('42') == 42

    def test_float_field(self):
        """Test Float field"""
        f = fields.Float(string='Price', digits=(10, 2))
        assert f.digits == (10, 2)
        assert f.convert_to_cache(3.14) == 3.14
        assert f.convert_to_cache('3.14') == 3.14

    def test_boolean_field(self):
        """Test Boolean field"""
        f = fields.Boolean(string='Active', default=True)
        assert f.get_default(None) is True
        assert f.convert_to_cache(True) is True
        assert f.convert_to_cache(False) is False
        assert f.convert_to_cache(None) is False


class TestDateTimeFields:
    """Test date and datetime fields"""

    def test_date_field(self):
        """Test Date field"""
        f = fields.Date(string='Birth Date')
        today = date.today()

        # Convert from date
        assert f.convert_to_cache(today) == today

        # Convert from string
        result = f.convert_to_cache('2024-01-15')
        assert isinstance(result, date)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

        # Convert from datetime
        dt = datetime(2024, 1, 15, 10, 30)
        result = f.convert_to_cache(dt)
        assert isinstance(result, date)
        assert result == date(2024, 1, 15)

    def test_datetime_field(self):
        """Test DateTime field"""
        f = fields.DateTime(string='Created At')
        now = datetime.now()

        # Convert from datetime
        assert f.convert_to_cache(now) == now

        # Convert from string - various formats
        result = f.convert_to_cache('2024-01-15 10:30:00')
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.hour == 10

        result = f.convert_to_cache('2024-01-15T10:30:00')
        assert isinstance(result, datetime)

    def test_date_to_database(self):
        """Test date conversion to database format"""
        f = fields.Date()
        d = date(2024, 1, 15)
        assert f.convert_to_database(d) == '2024-01-15'

    def test_datetime_to_database(self):
        """Test datetime conversion to database format"""
        f = fields.DateTime()
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = f.convert_to_database(dt)
        assert '2024-01-15' in result
        assert '10:30:45' in result


class TestSelectionField:
    """Test Selection field"""

    def test_selection_field_list(self):
        """Test Selection field with list"""
        choices = [('draft', 'Draft'), ('open', 'Open'), ('done', 'Done')]
        f = fields.Selection(selection=choices, string='State')
        assert f.selection == choices

    def test_selection_field_method(self):
        """Test Selection field with method name"""
        f = fields.Selection(selection='_get_states', string='State')
        assert f.selection == '_get_states'

    def test_selection_get_selection(self):
        """Test getting selection values"""
        choices = [('a', 'A'), ('b', 'B')]
        f = fields.Selection(selection=choices)

        # Mock model
        class MockModel:
            pass

        model = MockModel()
        assert f.get_selection(model) == choices


class TestRelationalFields:
    """Test relational fields"""

    def test_many2one_field(self):
        """Test Many2one field"""
        f = fields.Many2one('res.partner', string='Partner', ondelete='cascade')
        assert f.comodel_name == 'res.partner'
        assert f.ondelete == 'cascade'
        assert f.get_type_default() is None

    def test_one2many_field(self):
        """Test One2many field"""
        f = fields.One2many('res.partner', 'parent_id', string='Children')
        assert f.comodel_name == 'res.partner'
        assert f.inverse_name == 'parent_id'
        assert f.store is False
        assert f.get_type_default() == []

    def test_many2many_field(self):
        """Test Many2many field"""
        f = fields.Many2many(
            'res.partner',
            relation='partner_category_rel',
            column1='partner_id',
            column2='category_id',
            string='Categories'
        )
        assert f.comodel_name == 'res.partner'
        assert f.relation == 'partner_category_rel'
        assert f.column1 == 'partner_id'
        assert f.column2 == 'category_id'
        assert f.store is False
        assert f.get_type_default() == []


class TestFieldProperties:
    """Test field properties and features"""

    def test_field_required(self):
        """Test required field property"""
        f = fields.Char(required=True)
        f.name = 'test'
        with pytest.raises(ValueError, match="required"):
            f.validate(None)

    def test_field_readonly(self):
        """Test readonly field property"""
        f = fields.Char(readonly=True)
        assert f.readonly is True

    def test_field_copy(self):
        """Test copy field property"""
        f1 = fields.Char(copy=True)
        assert f1.copy is True

        f2 = fields.Char(copy=False)
        assert f2.copy is False

    def test_field_index(self):
        """Test index field property"""
        f = fields.Char(index=True)
        assert f.index is True

    def test_field_help(self):
        """Test help text"""
        f = fields.Char(help='This is a help text')
        assert f.help == 'This is a help text'

    def test_computed_field(self):
        """Test computed field"""
        f = fields.Char(compute='_compute_display_name', store=True, depends=['name', 'code'])
        assert f.compute == '_compute_display_name'
        assert f.store is True
        assert 'name' in f.depends
        assert 'code' in f.depends

    def test_computed_field_requires_depends(self):
        """Test that stored computed fields require depends"""
        with pytest.raises(ValueError, match="must specify depends"):
            fields.Char(compute='_compute_test', store=True)

    def test_related_field(self):
        """Test related field"""
        f = fields.Char(related='partner_id.name')
        assert f.related == 'partner_id.name'
        assert f.compute == '_compute_related'
        assert 'partner_id.name' in f.depends


class TestBinaryField:
    """Test Binary field"""

    def test_binary_field(self):
        """Test Binary field creation"""
        f = fields.Binary(string='Attachment', attachment=True)
        assert f.attachment is True

    def test_binary_field_no_attachment(self):
        """Test Binary field without attachment"""
        f = fields.Binary(attachment=False)
        assert f.attachment is False


class TestFieldColumnTypes:
    """Test field SQL column types"""

    def test_column_types(self):
        """Test that fields have correct column types"""
        assert fields.Char()._column_type == 'VARCHAR'
        assert fields.Text()._column_type == 'TEXT'
        assert fields.Integer()._column_type == 'INTEGER'
        assert fields.Float()._column_type == 'DOUBLE PRECISION'
        assert fields.Boolean()._column_type == 'BOOLEAN'
        assert fields.Date()._column_type == 'DATE'
        assert fields.DateTime()._column_type == 'TIMESTAMP'
        assert fields.Binary()._column_type == 'BYTEA'
        assert fields.Selection(selection=[])._column_type == 'VARCHAR'
        assert fields.Many2one('test')._column_type == 'INTEGER'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
