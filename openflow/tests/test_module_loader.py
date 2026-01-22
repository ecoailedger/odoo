"""
Test Module Loader System

Tests for module discovery, dependency resolution, and loading.
"""
import pytest
from pathlib import Path
from openflow.server.core.modules import (
    ModuleLoader,
    ModuleGraph,
    Module,
    ModuleManifest,
    ModuleState,
    CircularDependencyError,
    MissingDependencyError,
)


class TestModuleManifest:
    """Tests for ModuleManifest"""

    def test_manifest_from_dict(self):
        """Test creating manifest from dictionary"""
        data = {
            'name': 'Test Module',
            'version': '1.0',
            'depends': ['base'],
            'installable': True,
        }
        manifest = ModuleManifest.from_dict(data)

        assert manifest.name == 'Test Module'
        assert manifest.version == '1.0'
        assert manifest.depends == ['base']
        assert manifest.installable is True

    def test_manifest_to_dict(self):
        """Test converting manifest to dictionary"""
        manifest = ModuleManifest(
            name='Test Module',
            version='2.0',
            depends=['base', 'web'],
        )
        data = manifest.to_dict()

        assert data['name'] == 'Test Module'
        assert data['version'] == '2.0'
        assert data['depends'] == ['base', 'web']


class TestModuleGraph:
    """Tests for ModuleGraph and dependency resolution"""

    def test_add_module(self):
        """Test adding modules to graph"""
        graph = ModuleGraph()

        # Create test modules
        base = Module(
            name='base',
            path=Path('/tmp/base'),
            manifest=ModuleManifest(name='Base', depends=[]),
        )
        web = Module(
            name='web',
            path=Path('/tmp/web'),
            manifest=ModuleManifest(name='Web', depends=['base']),
        )

        graph.add_module(base)
        graph.add_module(web)

        assert 'base' in graph.modules
        assert 'web' in graph.modules
        assert 'web' in graph.graph['base']

    def test_topological_sort_simple(self):
        """Test topological sort with simple dependencies"""
        graph = ModuleGraph()

        # Create modules: base <- web <- sale
        base = Module(
            name='base',
            path=Path('/tmp/base'),
            manifest=ModuleManifest(name='Base', depends=[]),
        )
        web = Module(
            name='web',
            path=Path('/tmp/web'),
            manifest=ModuleManifest(name='Web', depends=['base']),
        )
        sale = Module(
            name='sale',
            path=Path('/tmp/sale'),
            manifest=ModuleManifest(name='Sale', depends=['base', 'web']),
        )

        graph.add_module(base)
        graph.add_module(web)
        graph.add_module(sale)

        result = graph.topological_sort()

        # base must come before web, and both before sale
        assert result.index('base') < result.index('web')
        assert result.index('base') < result.index('sale')
        assert result.index('web') < result.index('sale')

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        graph = ModuleGraph()

        # Create circular dependency: a -> b -> c -> a
        a = Module(
            name='a',
            path=Path('/tmp/a'),
            manifest=ModuleManifest(name='A', depends=['c']),
        )
        b = Module(
            name='b',
            path=Path('/tmp/b'),
            manifest=ModuleManifest(name='B', depends=['a']),
        )
        c = Module(
            name='c',
            path=Path('/tmp/c'),
            manifest=ModuleManifest(name='C', depends=['b']),
        )

        graph.add_module(a)
        graph.add_module(b)
        graph.add_module(c)

        with pytest.raises(CircularDependencyError):
            graph.topological_sort()

    def test_missing_dependency_detection(self):
        """Test detection of missing dependencies"""
        graph = ModuleGraph()

        # Create module with missing dependency
        module = Module(
            name='test',
            path=Path('/tmp/test'),
            manifest=ModuleManifest(name='Test', depends=['missing']),
        )

        graph.add_module(module)

        with pytest.raises(MissingDependencyError):
            graph.topological_sort()

    def test_dependency_chain(self):
        """Test getting dependency chain for a module"""
        graph = ModuleGraph()

        # Create chain: base <- web <- portal <- sale
        base = Module(
            name='base',
            path=Path('/tmp/base'),
            manifest=ModuleManifest(name='Base', depends=[]),
        )
        web = Module(
            name='web',
            path=Path('/tmp/web'),
            manifest=ModuleManifest(name='Web', depends=['base']),
        )
        portal = Module(
            name='portal',
            path=Path('/tmp/portal'),
            manifest=ModuleManifest(name='Portal', depends=['web']),
        )
        sale = Module(
            name='sale',
            path=Path('/tmp/sale'),
            manifest=ModuleManifest(name='Sale', depends=['portal', 'base']),
        )

        graph.add_module(base)
        graph.add_module(web)
        graph.add_module(portal)
        graph.add_module(sale)

        # Get dependency chain for sale
        chain = graph.get_dependency_chain('sale')

        # Should include all dependencies
        assert 'base' in chain
        assert 'web' in chain
        assert 'portal' in chain
        assert 'sale' in chain

        # Should be in correct order
        assert chain.index('base') < chain.index('web')
        assert chain.index('web') < chain.index('portal')
        assert chain.index('portal') < chain.index('sale')


class TestModuleLoader:
    """Tests for ModuleLoader"""

    def test_discover_base_module(self):
        """Test discovering the base module"""
        # Use actual addons path
        addons_path = Path(__file__).parent.parent / "openflow" / "openflow" / "server" / "addons"

        if not addons_path.exists():
            pytest.skip(f"Addons path not found: {addons_path}")

        loader = ModuleLoader([addons_path])
        modules = loader.discover_modules()

        # Base module should be discovered
        assert 'base' in modules
        assert modules['base'].manifest.name == 'Base'
        assert modules['base'].manifest.auto_install is True

    def test_build_dependency_graph(self):
        """Test building dependency graph"""
        addons_path = Path(__file__).parent.parent / "openflow" / "openflow" / "server" / "addons"

        if not addons_path.exists():
            pytest.skip(f"Addons path not found: {addons_path}")

        loader = ModuleLoader([addons_path])
        loader.discover_modules()
        loader.build_dependency_graph()

        # Graph should be built
        assert len(loader.graph.modules) > 0

    def test_get_load_order(self):
        """Test getting module load order"""
        addons_path = Path(__file__).parent.parent / "openflow" / "openflow" / "server" / "addons"

        if not addons_path.exists():
            pytest.skip(f"Addons path not found: {addons_path}")

        loader = ModuleLoader([addons_path])
        loader.discover_modules()
        loader.build_dependency_graph()

        load_order = loader.get_load_order()

        # Should return a list
        assert isinstance(load_order, list)

        # Base should be first (no dependencies)
        if 'base' in load_order:
            assert load_order[0] == 'base'


def test_module_state_enum():
    """Test ModuleState enum"""
    assert ModuleState.UNINSTALLED == "uninstalled"
    assert ModuleState.INSTALLED == "installed"
    assert ModuleState.TO_INSTALL == "to install"
    assert ModuleState.TO_UPGRADE == "to upgrade"
    assert ModuleState.TO_REMOVE == "to remove"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
