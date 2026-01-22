# OpenFlow

An open-source ERP framework inspired by Odoo, built with modern Python technologies.

## Overview

OpenFlow is a modular, extensible business application framework that provides a solid foundation for building enterprise resource planning (ERP) systems. It combines the power of FastAPI, SQLAlchemy, and PostgreSQL to deliver a high-performance, scalable platform.

## Features

- **Modular Architecture**: Plugin-based system similar to Odoo's addon structure
- **Modern Tech Stack**: Built on FastAPI with async support
- **ORM Layer**: Custom ORM built on SQLAlchemy with business logic support
- **Security**: Built-in authentication, authorization, and access control
- **Multi-tenancy**: Support for multiple databases and companies
- **REST API**: Full RESTful API for all resources
- **Background Jobs**: Celery integration for async task processing
- **Caching**: Redis integration for performance optimization
- **Extensible**: Easy to extend with custom modules

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Poetry (for dependency management)
- Docker & Docker Compose (for local development)

## Project Structure

```
/openflow
├── server/
│   ├── core/                 # Core framework (ORM, module loader, security)
│   ├── addons/               # Built-in modules (like Odoo's addons)
│   └── config/               # Server configuration
├── web/
│   ├── static/               # JS, CSS, assets
│   ├── templates/            # HTML templates
│   └── controllers/          # Web controllers
├── docs/                     # Documentation
├── tests/                    # Test suite
├── pyproject.toml           # Poetry configuration
├── docker-compose.yml       # Docker Compose configuration
└── Dockerfile               # Docker image definition
```

## Getting Started

### Using Docker (Recommended for Development)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd openflow
   ```

2. Start the development environment:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

4. View logs:
   ```bash
   docker-compose logs -f app
   ```

### Local Development (Without Docker)

1. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up PostgreSQL and Redis locally, then create a `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://openflow:password@localhost:5432/openflow
   REDIS_URL=redis://localhost:6379/0
   ENVIRONMENT=development
   DEBUG=true
   SECRET_KEY=your_secret_key_here
   ```

4. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```

5. Start the development server:
   ```bash
   poetry run uvicorn openflow.server.main:app --reload
   ```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=openflow --cov-report=html

# Run specific test file
poetry run pytest tests/test_core.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy openflow/
```

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## Architecture

### Core Components

1. **ORM Layer** (`server/core/orm/`): Custom ORM with business logic support
2. **Module System** (`server/core/modules/`): Dynamic module loading and management
3. **Security** (`server/core/security/`): Authentication, authorization, and access control
4. **API Layer** (`server/core/api/`): RESTful API framework
5. **Web Framework** (`web/`): Frontend controllers and views

### Addon Structure

Each addon follows this structure:

```
addons/my_module/
├── __init__.py
├── models/              # Database models
├── views/               # UI views
├── controllers/         # API endpoints
├── security/            # Access rights and rules
├── data/                # Initial data
└── static/              # Static assets
```

## Configuration

Configuration is managed through environment variables and the `server/config/` directory:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `ENVIRONMENT`: development/staging/production
- `DEBUG`: Enable debug mode

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Core ORM implementation
- [ ] Module loading system
- [ ] Security and access control
- [ ] Base addons (users, companies, partners)
- [ ] Web interface
- [ ] Report engine
- [ ] Workflow engine
- [ ] API documentation
- [ ] Admin panel

## Credits

Inspired by [Odoo](https://www.odoo.com/), this project aims to provide a modern, lightweight alternative with a focus on performance and developer experience.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Join our community discussions
