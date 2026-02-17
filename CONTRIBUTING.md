# Contributing to Adapterly

Thank you for your interest in contributing to Adapterly! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- PostgreSQL (optional, SQLite works for development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/samiveikko/adapterly.git
   cd adapterly
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start development servers**
   ```bash
   # Terminal 1: Django server
   python manage.py runserver

   # Terminal 2: FastAPI MCP server
   uvicorn fastapi_app.main:app --reload --port 8001
   ```

## Running Tests

### Django Tests
```bash
python manage.py test
```

### Specific App Tests
```bash
python manage.py test apps.accounts
python manage.py test apps.systems
python manage.py test apps.mcp
```

### With Coverage
```bash
pip install coverage
coverage run manage.py test
coverage report
```

## Code Style

We use the following tools to maintain code quality:

- **Ruff** - Fast Python linter and formatter
- **Black** - Code formatting (via Ruff)

### Running Linters

```bash
# Install ruff
pip install ruff

# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Style Guidelines

- Follow PEP 8
- Use type hints where practical
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new functionality
   - Update documentation if needed
   - Ensure all tests pass

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub.

5. **PR Review**
   - All PRs require at least one review
   - CI checks must pass
   - Address any feedback

## Adding New Adapters

To add a new system adapter:

1. Create a migration in `apps/systems/migrations/`
2. Define the System, Interface, Resources, and Actions
3. Test with real API credentials
4. Document any special authentication requirements

See existing adapters for examples.

## Adding Entity Types

To add new entity types for an industry:

1. Add EntityType to the relevant IndustryTemplate
2. Create default TermMappings for common systems
3. Document the entity schema

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Provide context about your environment

## Security

If you discover a security vulnerability, please email security@adapterly.io instead of opening a public issue.

## License

By contributing to Adapterly, you agree that your contributions will be licensed under the AGPL-3.0 license.

## Questions?

Feel free to open a Discussion on GitHub or reach out to the maintainers.
