# Django Skeleton

A modern Django boilerplate with HTMX, Alpine.js, and Tailwind CSS for rapid web application development.

## Features

- **Django 5.1+** - Latest Django with modular settings
- **HTMX** - High power tools for HTML, enabling modern UX without JavaScript complexity
- **Alpine.js** - Lightweight framework for composing JavaScript behavior
- **Tailwind CSS** - Utility-first CSS framework
- **PostgreSQL** - Production-ready database (SQLite for development)
- **Redis** - Caching and session storage
- **Celery** - Async task processing
- **Docker** - Complete containerization setup
- **Poetry** - Modern dependency management

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry (for dependency management)
- PostgreSQL (optional, SQLite used by default)
- Redis (optional, for caching)
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/django-skeleton.git
   cd django-skeleton
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run migrations**
   ```bash
   poetry run python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   poetry run python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   poetry run python manage.py runserver
   ```

   Visit http://localhost:8000 to see the application.

### Using Make Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make migrate        # Run migrations
make run           # Start development server
make test          # Run tests
make lint          # Run linting
make format        # Format code
```

## Docker Setup

### Development with Docker

1. **Build and start containers**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

   Visit http://localhost:8000

### Production with Docker

1. **Set production environment variables**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with production settings
   ```

2. **Build and run production containers**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

## Project Structure

```
django_skeleton/
├── apps/                  # Django applications
│   ├── common/           # Shared utilities and base classes
│   └── demo/            # Demo application
├── config/              # Project configuration
│   ├── settings/       # Modular settings
│   │   ├── base.py    # Base settings
│   │   ├── local.py   # Development settings
│   │   └── production.py  # Production settings
│   ├── urls.py        # URL configuration
│   ├── wsgi.py        # WSGI configuration
│   └── asgi.py        # ASGI configuration
├── templates/          # Project-wide templates
│   ├── base.html      # Base template
│   └── home.html      # Home page
├── static/            # Static files
│   ├── css/          # CSS files
│   └── js/           # JavaScript files
├── docs/             # Documentation
├── docker-compose.yml     # Docker development configuration
├── docker-compose.prod.yml  # Docker production configuration
├── Dockerfile            # Docker image definition
├── Makefile             # Make commands
├── manage.py            # Django management script
└── pyproject.toml       # Poetry configuration
```

## Tech Stack Details

### Backend
- **Django 5.1+** - Web framework
- **Django REST Framework** - API development
- **Celery** - Async task queue
- **Redis** - Caching and message broker
- **PostgreSQL** - Primary database
- **WhiteNoise** - Static file serving

### Frontend
- **HTMX** - Dynamic HTML interactions
- **Alpine.js** - Reactive components
- **Tailwind CSS** - Utility-first CSS

### Development Tools
- **Poetry** - Dependency management
- **pytest-django** - Testing framework
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking

## Demo Features

The skeleton includes a demo app showcasing:

- HTMX interactions (infinite scroll, inline editing, dynamic forms)
- Alpine.js components (modals, dropdowns, tabs)
- CRUD operations with Django
- Responsive design with Tailwind CSS
- Admin customization
- API endpoints

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `DEBUG` - Debug mode (True/False)
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DB_*` - Database configuration
- `REDIS_URL` - Redis connection URL
- `CELERY_*` - Celery configuration

## Testing

Run tests with pytest:
```bash
poetry run pytest
```

With coverage:
```bash
poetry run pytest --cov=apps --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - feel free to use this skeleton for your projects!

## Support

For issues and questions, please use the GitHub issue tracker.