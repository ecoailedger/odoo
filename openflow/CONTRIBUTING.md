# Contributing to OpenFlow

Thank you for your interest in contributing to OpenFlow! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/openflow.git
   cd openflow
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting
- **MyPy**: Type checking

Run all checks before committing:

```bash
# Format code
poetry run black .

# Lint
poetry run ruff check .

# Type check
poetry run mypy openflow/
```

## Testing

Write tests for all new features and bug fixes:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=openflow --cov-report=html

# Run specific test file
poetry run pytest tests/test_specific.py
```

## Commit Messages

Follow conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add user authentication module

- Implement JWT-based authentication
- Add login and logout endpoints
- Include password hashing
```

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them
3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request with:
   - Clear description of changes
   - Link to related issues
   - Screenshots (if applicable)
   - Test coverage

5. Wait for review and address feedback

## Module Development

When creating a new addon module:

```
openflow/server/addons/your_module/
├── __init__.py
├── __manifest__.py          # Module metadata
├── models/
│   ├── __init__.py
│   └── your_model.py
├── views/
│   └── your_view.xml
├── controllers/
│   ├── __init__.py
│   └── your_controller.py
├── security/
│   └── ir.model.access.csv
├── data/
│   └── initial_data.xml
└── tests/
    ├── __init__.py
    └── test_your_module.py
```

## Questions?

If you have questions or need help:

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Check existing issues and documentation first

Thank you for contributing!
