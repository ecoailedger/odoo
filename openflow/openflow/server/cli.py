"""
Command-line interface for OpenFlow
"""
import sys
import asyncio
from typing import Optional
import uvicorn

from openflow.server.config.settings import settings


def main():
    """Main CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="OpenFlow - Open-source ERP Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the web server")
    server_parser.add_argument(
        "--host",
        default=settings.host,
        help=f"Host to bind to (default: {settings.host})",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port to bind to (default: {settings.port})",
    )
    server_parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.debug,
        help="Enable auto-reload",
    )
    server_parser.add_argument(
        "--workers",
        type=int,
        default=settings.workers,
        help=f"Number of worker processes (default: {settings.workers})",
    )

    # Database command
    db_parser = subparsers.add_parser("db", help="Database operations")
    db_parser.add_argument(
        "action",
        choices=["init", "migrate", "reset"],
        help="Database action to perform",
    )

    # Shell command
    shell_parser = subparsers.add_parser("shell", help="Interactive Python shell")

    # Module command
    module_parser = subparsers.add_parser("module", help="Module operations")
    module_parser.add_argument(
        "action",
        choices=["list", "install", "upgrade", "uninstall", "update-list"],
        help="Module action to perform",
    )
    module_parser.add_argument(
        "modules",
        nargs="*",
        help="Module name(s) for install/upgrade/uninstall actions",
    )
    module_parser.add_argument(
        "--addons-path",
        default=None,
        help="Comma-separated list of addons paths",
    )

    args = parser.parse_args()

    if args.command == "server":
        run_server(
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
        )
    elif args.command == "db":
        run_db_command(args.action)
    elif args.command == "shell":
        run_shell()
    elif args.command == "module":
        run_module_command(args.action, args.modules, args.addons_path)
    else:
        parser.print_help()
        sys.exit(1)


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 4,
):
    """Start the web server"""
    print(f"Starting OpenFlow server on {host}:{port}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"Workers: {workers if not reload else 1}")
    print(f"Reload: {reload}")
    print("-" * 50)

    uvicorn.run(
        "openflow.server.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=settings.log_level.lower(),
    )


def run_db_command(action: str):
    """Run database commands"""
    from openflow.server.core.database import init_db, engine, Base

    async def _init_db():
        print("Initializing database...")
        await init_db()
        print("Database initialized successfully")

    async def _reset_db():
        print("WARNING: This will drop all tables!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            return

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("Dropped all tables")
            await conn.run_sync(Base.metadata.create_all)
            print("Recreated all tables")

    if action == "init":
        asyncio.run(_init_db())
    elif action == "reset":
        asyncio.run(_reset_db())
    elif action == "migrate":
        print("Running migrations...")
        import subprocess
        subprocess.run(["alembic", "upgrade", "head"])
    else:
        print(f"Unknown database action: {action}")
        sys.exit(1)


def run_module_command(action: str, modules: list, addons_path: Optional[str]):
    """Run module management commands"""
    from pathlib import Path
    from openflow.server.core.modules import module_registry

    # Get addons paths
    if addons_path:
        paths = [Path(p.strip()) for p in addons_path.split(",")]
    else:
        # Default addons path
        base_path = Path(__file__).parent / "addons"
        paths = [base_path]

    async def _list_modules():
        """List all available modules"""
        module_registry.initialize(paths)
        all_modules = module_registry.list_modules()

        print(f"\n{'Name':<20} {'Version':<10} {'State':<15} {'Summary':<50}")
        print("-" * 95)

        for mod in all_modules:
            print(
                f"{mod['name']:<20} {mod['version']:<10} "
                f"{mod['state']:<15} {mod['summary'][:47] + '...' if len(mod['summary']) > 50 else mod['summary']:<50}"
            )

        print(f"\nTotal: {len(all_modules)} modules")

    async def _install_modules():
        """Install specified modules"""
        if not modules:
            print("Error: No modules specified")
            sys.exit(1)

        from openflow.server.core.database import AsyncSessionLocal

        module_registry.initialize(paths)

        async with AsyncSessionLocal() as session:
            for module_name in modules:
                print(f"\nInstalling module: {module_name}")
                try:
                    await module_registry.install_module(
                        module_name, session, with_dependencies=True
                    )
                    print(f"✓ Successfully installed {module_name}")
                except Exception as e:
                    print(f"✗ Failed to install {module_name}: {e}")

    async def _update_module_list():
        """Update the list of available modules"""
        print("Updating module list...")
        module_registry.initialize(paths)
        modules_found = module_registry.discover_modules()
        print(f"✓ Found {len(modules_found)} modules")

    if action == "list":
        asyncio.run(_list_modules())
    elif action == "install":
        asyncio.run(_install_modules())
    elif action == "update-list":
        asyncio.run(_update_module_list())
    elif action == "upgrade":
        print("Module upgrade not yet implemented")
    elif action == "uninstall":
        print("Module uninstall not yet implemented")
    else:
        print(f"Unknown module action: {action}")
        sys.exit(1)


def run_shell():
    """Start an interactive Python shell"""
    try:
        from IPython import embed
        print("Starting OpenFlow interactive shell (IPython)")
        print("Available imports:")
        print("  - settings: Application settings")
        print("  - engine: Database engine")
        print("  - AsyncSessionLocal: Database session factory")
        print("  - module_registry: Module registry")
        print("-" * 50)

        from openflow.server.config.settings import settings
        from openflow.server.core.database import engine, AsyncSessionLocal
        from openflow.server.core.modules import module_registry

        embed(colors="neutral")
    except ImportError:
        import code
        print("Starting OpenFlow interactive shell (Python)")
        print("Available imports:")
        print("  - settings: Application settings")
        print("  - module_registry: Module registry")
        print("-" * 50)

        from openflow.server.config.settings import settings
        from openflow.server.core.modules import module_registry

        code.interact(local={"settings": settings, "module_registry": module_registry})


if __name__ == "__main__":
    main()
