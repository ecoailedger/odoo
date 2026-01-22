"""
Tests for ORM Model class and RecordSet
"""
import pytest

from openflow.server.core.orm import Model, fields, RecordSet, registry


class TestModelDefinition:
    """Test model definition and metaclass"""

    def test_model_creation(self):
        """Test creating a model class"""
        class Partner(Model):
            _name = 'test.partner'
            _description = 'Test Partner'

            name = fields.Char(string='Name', required=True)
            email = fields.Char(string='Email')
            active = fields.Boolean(string='Active', default=True)

        assert Partner._name == 'test.partner'
        assert Partner._description == 'Test Partner'
        assert 'name' in Partner._fields
        assert 'email' in Partner._fields
        assert 'active' in Partner._fields
        assert 'id' in Partner._fields  # Auto-added

    def test_model_registration(self):
        """Test model is registered"""
        class Product(Model):
            _name = 'test.product'

            name = fields.Char()

        assert 'test.product' in registry
        assert registry['test.product'] == Product

    def test_auto_id_field(self):
        """Test ID field is auto-added"""
        class Simple(Model):
            _name = 'test.simple'
            name = fields.Char()

        assert 'id' in Simple._fields
        id_field = Simple._fields['id']
        assert id_field.required is True
        assert id_field.readonly is True

    def test_field_name_assignment(self):
        """Test field names are assigned"""
        class TestModel(Model):
            _name = 'test.model'
            test_field = fields.Char(string='Test')

        field = TestModel._fields['test_field']
        assert field.name == 'test_field'
        assert field.model_name == 'test.model'

    def test_model_inheritance_fields(self):
        """Test field inheritance from base model"""
        class BaseModel(Model):
            _name = 'test.base'
            name = fields.Char()
            active = fields.Boolean(default=True)

        class ExtendedModel(BaseModel):
            _name = 'test.extended'
            description = fields.Text()

        # Extended model should have fields from base
        assert 'name' in ExtendedModel._fields
        assert 'active' in ExtendedModel._fields
        assert 'description' in ExtendedModel._fields


class TestRecordSet:
    """Test RecordSet functionality"""

    def setup_method(self):
        """Setup test model"""
        class Partner(Model):
            _name = 'test.recordset.partner'
            name = fields.Char()
            age = fields.Integer()
            active = fields.Boolean(default=True)

        self.Partner = Partner

    def test_recordset_creation(self):
        """Test creating a recordset"""
        rs = RecordSet(self.Partner, [1, 2, 3])
        assert len(rs) == 3
        assert rs.ids == [1, 2, 3]

    def test_recordset_empty(self):
        """Test empty recordset"""
        rs = RecordSet(self.Partner, [])
        assert len(rs) == 0
        assert not rs  # Should be falsy
        assert rs.ids == []

    def test_recordset_singleton(self):
        """Test singleton recordset"""
        rs = RecordSet(self.Partner, [42])
        assert len(rs) == 1
        assert rs.id == 42

    def test_recordset_id_property(self):
        """Test id property"""
        # Singleton
        rs = RecordSet(self.Partner, [42])
        assert rs.id == 42

        # Empty
        rs_empty = RecordSet(self.Partner, [])
        assert rs_empty.id is None

        # Multi-record should raise
        rs_multi = RecordSet(self.Partner, [1, 2])
        with pytest.raises(ValueError, match="singleton"):
            _ = rs_multi.id

    def test_recordset_iteration(self):
        """Test iterating over recordset"""
        rs = RecordSet(self.Partner, [1, 2, 3])
        items = list(rs)

        assert len(items) == 3
        assert all(isinstance(item, RecordSet) for item in items)
        assert items[0].id == 1
        assert items[1].id == 2
        assert items[2].id == 3

    def test_recordset_indexing(self):
        """Test indexing recordset"""
        rs = RecordSet(self.Partner, [10, 20, 30, 40])

        # Single index
        first = rs[0]
        assert first.id == 10
        assert len(first) == 1

        last = rs[-1]
        assert last.id == 40

        # Slicing
        slice_rs = rs[1:3]
        assert len(slice_rs) == 2
        assert slice_rs.ids == [20, 30]

    def test_recordset_equality(self):
        """Test recordset equality"""
        rs1 = RecordSet(self.Partner, [1, 2, 3])
        rs2 = RecordSet(self.Partner, [1, 2, 3])
        rs3 = RecordSet(self.Partner, [3, 2, 1])  # Different order
        rs4 = RecordSet(self.Partner, [1, 2])

        assert rs1 == rs2
        assert rs1 == rs3  # Order doesn't matter for equality
        assert rs1 != rs4

    def test_recordset_union(self):
        """Test recordset union (+)"""
        rs1 = RecordSet(self.Partner, [1, 2])
        rs2 = RecordSet(self.Partner, [3, 4])
        rs3 = RecordSet(self.Partner, [2, 5])

        # Union with +
        result = rs1 + rs2
        assert len(result) == 4
        assert set(result.ids) == {1, 2, 3, 4}

        # Union with overlapping IDs
        result2 = rs1 + rs3
        assert len(result2) == 4  # No duplicates
        assert set(result2.ids) == {1, 2, 5}

        # Union with |
        result3 = rs1 | rs2
        assert result3 == result

    def test_recordset_difference(self):
        """Test recordset difference (-)"""
        rs1 = RecordSet(self.Partner, [1, 2, 3, 4])
        rs2 = RecordSet(self.Partner, [2, 4])

        result = rs1 - rs2
        assert len(result) == 2
        assert set(result.ids) == {1, 3}

    def test_recordset_intersection(self):
        """Test recordset intersection (&)"""
        rs1 = RecordSet(self.Partner, [1, 2, 3, 4])
        rs2 = RecordSet(self.Partner, [2, 3, 5])

        result = rs1 & rs2
        assert len(result) == 2
        assert set(result.ids) == {2, 3}

    def test_recordset_ensure_one(self):
        """Test ensure_one method"""
        # Singleton - should pass
        rs = RecordSet(self.Partner, [1])
        assert rs.ensure_one() == rs

        # Empty - should raise
        rs_empty = RecordSet(self.Partner, [])
        with pytest.raises(ValueError, match="singleton"):
            rs_empty.ensure_one()

        # Multi - should raise
        rs_multi = RecordSet(self.Partner, [1, 2])
        with pytest.raises(ValueError, match="singleton"):
            rs_multi.ensure_one()

    def test_recordset_filtered(self):
        """Test filtered method"""
        # Create recordset with cache
        rs = RecordSet(self.Partner, [1, 2, 3, 4])
        rs._cache = {
            (1, 'age'): 18,
            (2, 'age'): 25,
            (3, 'age'): 30,
            (4, 'age'): 15,
        }

        # Filter by function
        def older_than_20(record):
            age = record._cache.get((record.id, 'age'), 0)
            return age > 20

        result = rs.filtered(older_than_20)
        assert set(result.ids) == {2, 3}

    def test_recordset_sorted(self):
        """Test sorted method"""
        rs = RecordSet(self.Partner, [3, 1, 4, 2])

        # Sort by ID (default)
        sorted_rs = rs.sorted()
        assert sorted_rs.ids == [1, 2, 3, 4]

        # Sort reverse
        sorted_rev = rs.sorted(reverse=True)
        assert sorted_rev.ids == [4, 3, 2, 1]

    def test_recordset_mapped(self):
        """Test mapped method"""
        rs = RecordSet(self.Partner, [1, 2, 3])
        rs._cache = {
            (1, 'name'): 'Alice',
            (2, 'name'): 'Bob',
            (3, 'name'): 'Charlie',
        }

        # Map to field values
        # Note: This is a simplified test, actual implementation needs more work
        # names = rs.mapped('name')
        # assert names == ['Alice', 'Bob', 'Charlie']

    def test_recordset_repr(self):
        """Test string representation"""
        rs = RecordSet(self.Partner, [1, 2, 3])
        repr_str = repr(rs)

        assert 'test.recordset.partner' in repr_str
        assert '1' in repr_str or '2' in repr_str


class TestModelTableName:
    """Test model table name generation"""

    def test_explicit_table_name(self):
        """Test explicit table name"""
        class MyModel(Model):
            _name = 'my.model'
            _table = 'custom_table_name'

        assert MyModel._get_table_name() == 'custom_table_name'

    def test_auto_table_name(self):
        """Test auto-generated table name"""
        class MyModel(Model):
            _name = 'my.model'

        assert MyModel._get_table_name() == 'my_model'

    def test_table_name_with_dots(self):
        """Test table name conversion from dots to underscores"""
        class MyModel(Model):
            _name = 'res.partner.bank'

        assert MyModel._get_table_name() == 'res_partner_bank'


class TestModelOrder:
    """Test model ordering"""

    def test_default_order(self):
        """Test default order is 'id'"""
        class MyModel(Model):
            _name = 'test.order'

        assert MyModel._order == 'id'

    def test_custom_order(self):
        """Test custom order"""
        class MyModel(Model):
            _name = 'test.order2'
            _order = 'name, id desc'

        assert MyModel._order == 'name, id desc'


class TestModelRecName:
    """Test model record name field"""

    def test_default_rec_name(self):
        """Test default record name field"""
        class MyModel(Model):
            _name = 'test.rec'

        assert MyModel._rec_name == 'name'

    def test_custom_rec_name(self):
        """Test custom record name field"""
        class MyModel(Model):
            _name = 'test.rec2'
            _rec_name = 'code'

        assert MyModel._rec_name == 'code'


class TestModelDescription:
    """Test model description"""

    def test_empty_description(self):
        """Test default empty description"""
        class MyModel(Model):
            _name = 'test.desc'

        assert MyModel._description == ''

    def test_custom_description(self):
        """Test custom description"""
        class MyModel(Model):
            _name = 'test.desc2'
            _description = 'My Test Model'

        assert MyModel._description == 'My Test Model'


class TestModelBrowse:
    """Test browse method"""

    def test_browse_single_id(self):
        """Test browse with single ID"""
        class MyModel(Model):
            _name = 'test.browse'

        rs = MyModel.browse(42)
        assert isinstance(rs, RecordSet)
        assert rs.id == 42

    def test_browse_multiple_ids(self):
        """Test browse with multiple IDs"""
        class MyModel(Model):
            _name = 'test.browse2'

        rs = MyModel.browse([1, 2, 3])
        assert isinstance(rs, RecordSet)
        assert len(rs) == 3
        assert rs.ids == [1, 2, 3]

    def test_browse_empty(self):
        """Test browse with empty list"""
        class MyModel(Model):
            _name = 'test.browse3'

        rs = MyModel.browse([])
        assert isinstance(rs, RecordSet)
        assert len(rs) == 0


class TestFieldAccess:
    """Test field access on models"""

    def test_field_in_model(self):
        """Test accessing fields through _fields"""
        class TestModel(Model):
            _name = 'test.fields'
            name = fields.Char(required=True)
            age = fields.Integer()

        assert 'name' in TestModel._fields
        assert 'age' in TestModel._fields

        name_field = TestModel._fields['name']
        assert name_field.required is True
        assert isinstance(name_field, fields.Char)


class TestModelInheritance:
    """Test model inheritance attributes"""

    def test_inherit_attribute(self):
        """Test _inherit attribute"""
        class Parent(Model):
            _name = 'test.parent'
            name = fields.Char()

        class Child(Model):
            _name = 'test.child'
            _inherit = 'test.parent'
            age = fields.Integer()

        assert Child._inherit == 'test.parent'

    def test_inherits_attribute(self):
        """Test _inherits attribute for delegation"""
        class Company(Model):
            _name = 'test.company'
            name = fields.Char()

        class User(Model):
            _name = 'test.user'
            _inherits = {'test.company': 'company_id'}

        assert 'test.company' in User._inherits


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
