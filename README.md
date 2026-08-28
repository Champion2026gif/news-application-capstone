# News Application Capstone

A Django News Application with role-based accounts for Readers, Journalists, and Editors.

The application supports user registration, role-specific dashboards, article submission and editorial approval, newsletters, a REST API, Sphinx documentation, and Docker.

## Features

- Reader, Journalist, and Editor registration
- Role-specific dashboards
- Journalists can create and submit articles
- Editors can review, approve, or reject submitted articles
- Readers can browse approved articles
- Newsletter support
- REST API
- Sphinx-generated documentation
- Docker support

## Requirements

- Python 3.12
- Git
- Docker Desktop (for Docker setup)

MariaDB is optional. By default, the application can run using SQLite.

## Clone the Repository

```bash
git clone https://github.com/Champion2026gif/news-application-capstone.git
cd news-application-capstone
```

## Run with a Python Virtual Environment

Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Apply the database migrations:

```powershell
python manage.py migrate
```

Create the application role groups:

```powershell
python manage.py setup_groups
```

Run the automated tests:

```powershell
python manage.py test
```

Start the development server:

```powershell
python manage.py runserver
```

Open the application in your browser at `http://127.0.0.1:8000/`.

Users can register as a Reader, Journalist, or Editor and will be directed to the appropriate role-specific dashboard.

## Run with Docker

Build the Docker image:

```bash
docker build -t news-application .
```

Run the container:

```bash
docker run --rm -p 8000:8000 news-application
```

Open the application in your browser at `http://localhost:8000/`.

The Docker image applies the Django migrations and creates the required role groups during the image build.

## Sphinx Documentation

The Sphinx source files and generated documentation are stored in the `docs` directory.

To rebuild the HTML documentation:

```bash
sphinx-build -b html docs/source docs/build/html
```

The generated documentation can then be opened from:

```text
docs/build/html/index.html
```

## Optional MariaDB Configuration

The application can optionally use MariaDB.

Set the required database environment variables before running migrations. Do not commit database passwords or other secrets to the repository.

Example environment variables include:

```text
USE_MARIADB=1
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

When `USE_MARIADB` is enabled, Django uses the MariaDB-compatible database configuration.

## Project Structure

```text
accounts/       User accounts, registration, roles, and dashboards
api/            REST API
articles/       Articles, newsletters, and editorial workflow
docs/           Sphinx documentation
news_project/   Django project configuration
templates/      HTML templates
Dockerfile      Docker image configuration
manage.py       Django management utility
requirements.txt Python dependencies
```

## Git Branches

The project uses the following branches as part of the capstone workflow:

- `main` - completed working project
- `docs` - documentation and Sphinx work
- `container` - Docker configuration

## Testing

The project includes an automated Django test suite.

Run:

```bash
python manage.py test
```

The final project validation completed successfully with 50 tests passing.

## Security

Passwords, database credentials, API keys, and other secrets should not be committed to this public repository. Use environment variables for sensitive configuration.