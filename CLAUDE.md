# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenFlow is an open-source ERP framework inspired by Odoo, built with FastAPI, SQLAlchemy, and PostgreSQL. The project implements a modular, plugin-based architecture for building enterprise resource planning systems.

**Repository Location**: All code is in the `openflow/` subdirectory of this repository.

## Critical Directory Structure Notes

The project has an unusual directory structure with duplicate directories:

**Server Directories**:
- `/openflow/openflow/server/` - **Primary location** with complete core framework
- `/openflow/server/` - Partial directory with some configuration files

**Web Directories**:
- `/openflow/web/` - **Active frontend** with static files (HTML, JS, CSS)
- `/openflow/openflow/web/` - Contains controllers only (backend web controllers)

**API Entry Point**:
- `/openflow/api/index.py` - Vercel serverless function entry point (imports from `openflow.server.main`)

The API module was initially missing from the primary location and has been copied to `/openflow/openflow/server/core/api/`.

## Development Commands

### Setup & Installation

```bash
cd openflow
poetry install
cp .env.example .env
# Edit .env with your database credentials
```

### Running the Application

```bash
# Development server with auto-reload
cd openflow
poetry run uvicorn openflow.server.main:app --reload

# Using the CLI
poetry run openflow server --reload

# Production server
poetry run openflow server --workers 4
```

### Database Operations

```bash
# Initialize database (create tables)
poetry run openflow db init

# Run Alembic migrations
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Reset database (WARNING: drops all data)
poetry run openflow db reset
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=openflow --cov-report=html

# Run specific test file
poetry run pytest tests/test_orm_models.py

# Run specific test function
poetry run pytest tests/test_orm_models.py::test_model_creation
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy openflow/

# Run all quality checks
poetry run black . && poetry run ruff check . && poetry run mypy openflow/
```

### Module Management

```bash
# List available modules
poetry run openflow module list

# Install a module
poetry run openflow module install <module_name>

# Update module list
poetry run openflow module update-list
```

### Interactive Shell

```bash
# Start IPython shell with OpenFlow context
poetry run openflow shell
```

### Docker Development

```bash
cd openflow

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build
```

## Architecture Overview

### Core Framework Components

#### 1. ORM System (`openflow/server/core/orm/`)

Custom ORM built on SQLAlchemy with business logic support:

- **models.py** - Base `Model` class with metaclass-based auto-registration
- **fields.py** - Field types: Char, Text, Integer, Float, Boolean, Date, DateTime, Binary, Selection, Many2one, One2many, Many2many
- **registry.py** - `ModelRegistry` singleton for global model management
- **recordset.py** - `RecordSet` objects for efficient record manipulation
- **domain.py** - Domain query language parser (translates to SQL WHERE clauses)

**Key Pattern**: Models auto-register via `ModelMetaclass` when defined. Access via `env['model.name']`.

```python
from openflow.server.core.orm import Model, fields

class Partner(Model):
    _name = 'res.partner'
    _description = 'Partner'

    name = fields.Char(required=True)
    email = fields.Char()
    active = fields.Boolean(default=True)
```

#### 2. Module System (`openflow/server/core/modules/`)

Plugin-based architecture similar to Odoo's addon system:

- **loader.py** - Module discovery and topological sort for dependency resolution
- **registry.py** - `ModuleRegistry` manages module lifecycle
- **module.py** - Module and ModuleManifest classes
- **data_loader.py** - XML/CSV data loading with external ID management

**Module Structure**: Each addon in `openflow/server/addons/` has:
- `__manifest__.py` - Metadata (name, version, dependencies, auto_install)
- `models/` - Python model definitions
- `views/` - XML view definitions
- `data/` - Initial data files
- `security/` - Access control definitions

**Auto-install**: Modules with `'auto_install': True` load automatically on startup (e.g., `base` module).

#### 3. Security System (`openflow/server/core/security/`)

Comprehensive authentication and authorization:

- **jwt_handler.py** - JWT token creation and validation
- **password.py** - Password hashing (bcrypt via passlib)
- **session.py** - Session management with Redis
- **access_control.py** - Model and record-level access control (RBAC)
- **decorators.py** - `@require_auth` and similar decorators
- **exceptions.py** - Security exceptions

**Key Classes**: `AccessController` for checking CRUD permissions, record rules for row-level security.

#### 4. View System (`openflow/server/core/views/`)

XML-based UI definition system with inheritance (14,020 lines documented in `docs/VIEW_SYSTEM.md`):

- **parser.py** - XML view parsing to Python dict
- **renderer.py** - View rendering to JSON for frontend
- **inheritance.py** - XPath-based view inheritance
- **validator.py** - View validation against model schema

**View Types**: form, tree (list), kanban, calendar, graph, pivot, search

#### 5. API Layer (`openflow/server/core/api/`)

Dual API approach:

- **jsonrpc.py** - JSON-RPC 2.0 endpoint (`/jsonrpc`)
- **rest.py** - RESTful CRUD endpoints (`/api/v1/{model}`)
- **router.py** - Dynamic FastAPI router creation per model
- **serializers.py** - Record serialization to JSON
- **dependencies.py** - FastAPI dependencies (get_env, get_current_user)
- **exceptions.py** - API exceptions

**Usage**: Both APIs provide full CRUD operations on all registered models.

#### 6. Web Client (`openflow/web/`)

Vanilla JavaScript frontend using ES6 modules (no build step required):

**Directory Structure**:
- `web/static/index.html` - Main HTML entry point
- `web/static/js/` - JavaScript modules
  - `app.js` - Main application class, layout, routing
  - `rpc_service.js` - Backend communication (JSON-RPC & REST)
  - `action_manager.js` - Action handling and view orchestration
  - `view_manager.js` - View loading and rendering
  - `view_renderer.js` - View-specific rendering logic
  - `field_widgets.js` - Form field widgets
  - `notification.js` - Toast notifications
- `web/static/css/app.css` - Application styles

**Architecture**:
- **No build process**: Pure ES6 modules served directly
- **RPC Communication**: Singleton `rpc` service handles all backend calls
- **Authentication**: JWT tokens stored in localStorage
- **View System**: Dynamically renders form, tree, and other view types
- **Event-driven**: Uses CustomEvents for cross-component communication

**Key Classes**:
- `OpenFlowApp` - Main app initialization, layout, auth flow
- `RPCService` - Handles both JSON-RPC (`/jsonrpc`) and REST API (`/api/v1`) calls
- `ActionManager` - Executes actions (open views, run wizards, etc.)
- `ViewManager` - Loads view definitions and orchestrates rendering

**Static File Serving**: FastAPI serves `/static/*` from `web/static/` directory.

### Configuration (`openflow/server/config/`)

**settings.py** - Pydantic-based settings with environment variable support

**Key Environment Variables**:
- `DATABASE_URL` - PostgreSQL connection (format: `postgresql+asyncpg://user:pass@host:port/db`)
- `REDIS_URL` - Redis for caching and Celery
- `SECRET_KEY` - JWT signing key
- `ENVIRONMENT` - development/staging/production
- `DEBUG` - Enable debug mode and API docs

**Database Configuration Issue**: In development mode, the code uses `NullPool` (no connection pooling) to avoid connection issues. Do not specify `pool_size` or `max_overflow` when using `NullPool`.

### Built-in Addons (`openflow/server/addons/`)

7 pre-built modules demonstrating addon patterns:

1. **base** - Core models (users, groups, companies, partners, countries, currencies)
2. **auth** - Advanced authentication and session management
3. **helpdesk** - Ticket/issue tracking system
4. **mail** - Email and messaging system
5. **stock** - Inventory management
6. **account** - Accounting and financial management
7. **repair** - Equipment repair management

### Entry Points

**main.py** - FastAPI application with lifespan events:
- Startup: Initialize database, load auto-install modules
- Includes CORS middleware, static file serving
- Exposes `/docs` (Swagger) and `/redoc` in debug mode

**cli.py** - Command-line interface via `poetry run openflow`:
- `server` - Start web server
- `db` - Database operations
- `shell` - Interactive Python shell
- `module` - Module management

## Important Implementation Notes

### Async/Await

The entire framework is async-first:
- Use `AsyncSession` for database operations
- All ORM operations are async: `await model.create()`, `await model.search()`
- FastAPI endpoints are async functions

### Model Registration

Models register automatically via metaclass when imported:
```python
# Model definition triggers registration
class MyModel(Model):
    _name = 'my.model'
    ...

# Access via environment
env = get_env()
my_model = env['my.model']  # Returns the model class
records = await my_model.search([('field', '=', 'value')])
```

### Domain Query Language

Search uses Odoo-style domain syntax:
```python
# Simple query
records = await model.search([('name', '=', 'John')])

# Complex query with operators
records = await model.search([
    ('age', '>', 18),
    ('active', '=', True),
    '|',  # OR operator
    ('city', '=', 'NYC'),
    ('city', '=', 'LA')
])
```

**Operators**: `=`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`, `like`, `ilike`, `=like`, `=ilike`

### Record Access

Records and RecordSets provide dict-like and attribute access:
```python
partner = await Partner.browse([1])
print(partner.name)  # Attribute access
print(partner['name'])  # Dict access

# Multiple records
partners = await Partner.search([('active', '=', True)])
for partner in partners:
    print(partner.name)
```

### View Inheritance

Views can extend parent views using XPath:
```xml
<record id="view_partner_form_inherit" model="ir.ui.view">
    <field name="name">res.partner.form.inherit</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='email']" position="after">
            <field name="phone"/>
        </xpath>
    </field>
</record>
```

## Vercel Deployment Considerations

**Important**: This application is designed as a traditional server application with persistent database connections and background workers (Celery). Vercel's serverless architecture may not be ideal for this type of application.

**Challenges**:
1. **Database Connection Pooling**: Serverless functions should use connection pooling services (e.g., PgBouncer)
2. **Celery Workers**: Background tasks require separate worker processes (not supported on Vercel)
3. **Redis**: Requires external Redis service (e.g., Upstash, Redis Cloud)
4. **File Storage**: Ephemeral filesystem requires external storage (e.g., S3, Cloudflare R2)

**For Vercel Deployment**:
- Use Vercel Postgres or external PostgreSQL with connection pooling
- Use external Redis (Upstash Redis)
- Disable Celery workers or use external worker service
- Set `ENVIRONMENT=production` and proper `SECRET_KEY`
- Consider switching to Vercel-native serverless patterns if possible

**Vercel Configuration** (`vercel.json`):
- Entry point: `api/index.py` - Serverless function handler
- Routes all requests through FastAPI app
- Static files served from `web/static/` (accessible at `/static/*`)
- Environment variables configured for production mode

**Frontend Considerations**:
- Vanilla JS frontend requires no build step - works on Vercel out of the box
- All static assets (HTML, JS, CSS) served directly from `web/static/`
- Frontend accesses backend via `/jsonrpc` and `/api/v1/*` endpoints
- CORS middleware configured in `main.py` for cross-origin requests

**Alternative**: Consider deploying to platforms better suited for traditional apps:
- Railway.app
- Render.com
- DigitalOcean App Platform
- Fly.io
- Heroku

## Common Workflows

### Adding a New Model

1. Create model file in addon's `models/` directory
2. Define model class inheriting from `Model`
3. Set `_name`, `_description`, and fields
4. Import in addon's `__init__.py`
5. Restart server (auto-reload picks it up)
6. Run `alembic revision --autogenerate` to create migration
7. Run `alembic upgrade head` to apply

### Creating a New Module

1. Create directory in `openflow/server/addons/`
2. Create `__manifest__.py` with metadata
3. Create `__init__.py` for imports
4. Add subdirectories: `models/`, `views/`, `data/`, `security/`
5. Install: `poetry run openflow module install <module_name>`

### Debugging

- Enable `DEBUG=true` in `.env` for detailed logs
- Use `DATABASE_ECHO=true` to see SQL queries
- Access API docs at `http://localhost:8000/docs`
- Use IPython shell for interactive testing: `poetry run openflow shell`

### Working with the Frontend

**Development**:
1. Start the backend server: `cd openflow && poetry run uvicorn openflow.server.main:app --reload`
2. Access the web client at `http://localhost:8000/static/index.html`
3. Open browser DevTools to debug JavaScript
4. No build step required - edit JS/CSS files and refresh browser

**Frontend Files**:
- All frontend code is in `openflow/web/static/`
- Edit JS modules directly - they're loaded as ES6 modules
- Changes take effect immediately on browser refresh
- FastAPI serves static files from `/static/*` URL path

**Testing Frontend-Backend Integration**:
- Use browser DevTools Console to access `window.rpc` service
- Example: `await rpc.search('res.partner', [], {limit: 10})`
- Check Network tab to inspect JSON-RPC and REST API calls
- Authentication tokens stored in localStorage (key: `auth_token`)

**Adding New Views**:
1. Create view definition in backend (`views/` in addon)
2. Load view via `ActionManager.doAction()` from frontend
3. Views are rendered dynamically using `view_renderer.js`

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Web Framework | FastAPI | 0.109+ |
| ASGI Server | Uvicorn | 0.27+ |
| ORM | SQLAlchemy | 2.0+ |
| Database Driver | asyncpg | 0.29+ |
| Database | PostgreSQL | 15+ |
| Migration | Alembic | 1.13+ |
| Task Queue | Celery | 5.3+ |
| Cache/Broker | Redis | 7+ |
| Auth | python-jose | 3.3+ |
| Password | passlib[bcrypt] | 1.7+ |
| Validation | Pydantic | 2.5+ |
| XML Processing | lxml | 5.1+ |
| Testing | pytest + pytest-asyncio | 7.4+/0.23+ |
| Code Format | Black | 24+ |
| Linting | Ruff | 0.1+ |
| Type Checking | MyPy | 1.8+ |

### Frontend

| Component | Technology | Notes |
|-----------|------------|-------|
| JavaScript | ES6 Modules | Native browser support, no transpiling |
| CSS | Vanilla CSS | No preprocessor |
| Build Tool | None | Direct file serving |
| API Communication | Fetch API | JSON-RPC 2.0 & REST |
| State Management | Vanilla JS | Class-based architecture |
| Module System | ES6 import/export | Browser-native modules |

## Files Not to Modify

- `poetry.lock` - Regenerate with `poetry lock` if needed
- `alembic/versions/*` - Migration files (create new ones, don't edit)
- `.venv/` - Virtual environment (Poetry managed)

## Known Issues & Fixes

1. **Database Pool Configuration**: Fixed - production uses pooling, development uses NullPool
2. **Missing API Module**: Fixed - copied from `/openflow/server/core/api/` to proper location
3. **Duplicate Server Directories**: Be aware of `/openflow/server/` vs `/openflow/openflow/server/`

## Testing Strategy

- **Unit Tests**: Test individual components (ORM, fields, domain parser)
- **Integration Tests**: Test API endpoints with test database
- **Module Tests**: Test module loading and data installation
- **Security Tests**: Test authentication, authorization, access control

**Test Database**: Configure separate test database in `.env.test` or use in-memory SQLite for unit tests.

## Performance Notes

- **Connection Pooling**: Production uses connection pooling for efficiency
- **Async Operations**: All I/O is async for high concurrency
- **Redis Caching**: Cache frequently accessed data in Redis
- **Lazy Loading**: Related records loaded on-demand
- **Recordset Operations**: Batch operations when possible to minimize queries

## Documentation References

- **VIEW_SYSTEM.md**: Comprehensive view system documentation (14,020 lines)
- **README.md**: Project overview and quick start
- **API Docs**: Available at `/docs` when `DEBUG=true`

## Git Workflow

Always work on feature branches:
```bash
git checkout -b feature/description
# Make changes
git add .
git commit -m "feat: description"
git push origin feature/description
```

For this repository, work on branches matching: `claude/<feature-name>-<session-id>`
