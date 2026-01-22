"""
Manual test for module loader system
"""
from pathlib import Path
from openflow.server.core.modules import ModuleLoader, module_registry

def test_module_discovery():
    """Test module discovery"""
    print("Testing module discovery...")

    addons_path = Path(__file__).parent / "openflow" / "server" / "addons"
    print(f"Addons path: {addons_path}")
    print(f"Addons path exists: {addons_path.exists()}")

    if not addons_path.exists():
        print("ERROR: Addons path does not exist!")
        return False

    loader = ModuleLoader([addons_path])
    modules = loader.discover_modules()

    print(f"\nDiscovered {len(modules)} modules:")
    for name, module in modules.items():
        print(f"  - {name}: {module.manifest.name} v{module.manifest.version}")
        print(f"    Depends: {module.manifest.depends}")
        print(f"    Auto-install: {module.manifest.auto_install}")

    return len(modules) > 0


def test_dependency_resolution():
    """Test dependency resolution"""
    print("\n" + "="*60)
    print("Testing dependency resolution...")

    addons_path = Path(__file__).parent / "openflow" / "server" / "addons"

    loader = ModuleLoader([addons_path])
    loader.discover_modules()
    loader.build_dependency_graph()

    print("\nComputing load order...")
    try:
        load_order = loader.get_load_order()
        print(f"Load order: {load_order}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_module_registry():
    """Test module registry"""
    print("\n" + "="*60)
    print("Testing module registry...")

    addons_path = Path(__file__).parent / "openflow" / "server" / "addons"

    module_registry.initialize([addons_path])

    print(f"\nModule registry initialized with {len(module_registry.modules)} modules")

    # List all modules
    all_modules = module_registry.list_modules()
    print("\nAll modules:")
    for mod in all_modules:
        print(f"  - {mod['name']}: {mod['summary']}")

    # Get base module
    base = module_registry.get_module('base')
    if base:
        print(f"\nBase module found:")
        print(f"  Name: {base.manifest.name}")
        print(f"  Version: {base.manifest.version}")
        print(f"  Auto-install: {base.manifest.auto_install}")
        print(f"  Depends: {base.manifest.depends}")

    return True


def test_module_loading():
    """Test module loading"""
    print("\n" + "="*60)
    print("Testing module loading...")

    addons_path = Path(__file__).parent / "openflow" / "server" / "addons"

    module_registry.initialize([addons_path])

    print("\nAttempting to load base module...")
    try:
        module_registry.load_modules(['base'])
        print("✓ Successfully loaded base module")

        # Check if models were registered
        from openflow.server.core.orm import ModelRegistry as ORMRegistry
        orm_registry = ORMRegistry()

        model_names = list(orm_registry.keys())
        print(f"\nRegistered models: {len(model_names)}")
        for model_name in sorted(model_names):
            print(f"  - {model_name}")

        return True
    except Exception as e:
        print(f"✗ Failed to load base module: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("OpenFlow Module Loader Test Suite")
    print("="*60)

    results = []

    results.append(("Module Discovery", test_module_discovery()))
    results.append(("Dependency Resolution", test_dependency_resolution()))
    results.append(("Module Registry", test_module_registry()))
    results.append(("Module Loading", test_module_loading()))

    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)
    print("\n" + "="*60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("="*60)
