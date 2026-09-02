# News Application Capstone

A Django News Application with role-based accounts for Readers,
Journalists, and Editors.

The application supports user registration, role-specific dashboards,
article submission and editorial approval, newsletters, a REST API,
Sphinx documentation, and Docker.

## Features

-   Reader, Journalist, and Editor registration
-   Role-specific dashboards
-   Journalists can create and submit articles
-   Editors can review, approve, or reject submitted articles
-   Readers can browse approved articles
-   Newsletter support
-   REST API
-   Sphinx-generated documentation
-   Docker Compose support with MariaDB

## Requirements

### Standard local installation

-   Python 3.12
-   Git
-   MariaDB Server

### Docker installation

-   Git
-   Docker Desktop

MariaDB/MySQL is the default database for this application. SQLite
should only be used as an optional lightweight development/testing
alternative.

## Standard Local Installation with MariaDB

### 1. Clone the Repository

``` bash
git clone https://github.com/Champion2026gif/news-application-capstone.git
cd news-application-capstone
```

### 2. Create and Activate a Python Virtual Environment

#### Windows PowerShell

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install the Dependencies

``` powershell
python -m pip install -r requirements.txt
```

### 4. Create the MariaDB Database

Make sure MariaDB Server is installed and running.

Connect to MariaDB as the root user:

``` powershell
mariadb -u root -p
```

If `mariadb` is not available on the Windows PATH, run the executable
using its full installation path. For example:

``` powershell
& "C:\Program Files\MariaDB 12.3\bin\mariadb.exe" -u root -p
```

The MariaDB version/folder name may be different on another computer.

Enter the MariaDB root password when prompted.

At the `MariaDB [(none)]>` prompt, create the application database and
database user:

``` sql
CREATE DATABASE news_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'news_user'@'localhost'
IDENTIFIED BY 'your_database_password';

GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';

FLUSH PRIVILEGES;

EXIT;
```

Replace `your_database_password` with your own secure password.

If `news_db` or `news_user` already exists, do not recreate it. Update
the existing user password if required and make sure the `.env`
credentials match.

### 5. Configure Environment Variables

Create a file named `.env` in the same directory as `manage.py`.

Use `.env.example` as a template:

``` text
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=your_database_password
DB_ROOT_PASSWORD=your_docker_root_password
DB_HOST=localhost
DB_PORT=3306

DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
```

Replace the placeholder values with your own credentials.

`DB_PASSWORD` must match the password assigned to `news_user`.

`DB_ROOT_PASSWORD` is used by the Docker MariaDB service. It may be set
even when using the standard local installation so the same `.env` file
can also be used with Docker.

The `.env` file contains sensitive information and must not be committed
to the repository.

### 6. Apply Database Migrations

Only run migrations after the MariaDB database and `.env` file have been
configured.

``` powershell
python manage.py migrate
```

### 7. Create the Application Role Groups

``` powershell
python manage.py setup_groups
```

### 8. Run the Automated Tests

``` powershell
python manage.py test
```

### 9. Start the Development Server

``` powershell
python manage.py runserver
```

Open the application in a browser at:

``` text
http://127.0.0.1:8000/
```

Users can register as a Reader, Journalist, or Editor and will be
directed to the appropriate role-specific dashboard.

To stop the Django development server, return to the terminal and press
`Ctrl+C`.

## Run with Docker

Docker is a separate installation path. Users who choose Docker do not
need to perform the manual MariaDB setup above because Docker Compose
creates and runs the MariaDB service.

### 1. Clone the Repository

``` bash
git clone https://github.com/Champion2026gif/news-application-capstone.git
cd news-application-capstone
```

### 2. Start Docker Desktop

Install Docker Desktop if necessary.

Open Docker Desktop and wait until the Docker engine is running before
continuing.

### 3. Configure the Docker Environment

Create a `.env` file in the project directory, in the same location as
`manage.py`, `Dockerfile`, and `docker-compose.yml`.

Use `.env.example` as the template and provide your own private values:

``` text
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=your_database_password
DB_ROOT_PASSWORD=your_docker_root_password
DB_HOST=localhost
DB_PORT=3306

DJANGO_SECRET_KEY=your_secret_key
DJANGO_DEBUG=True
```

Do not commit the real `.env` file.

Docker Compose overrides the database host for the Django container so
that Django connects to the MariaDB `db` service.

### 4. Build the Docker Images

From the directory containing `docker-compose.yml`, run:

``` powershell
docker compose build
```

### 5. Start the Containers

``` powershell
docker compose up -d
```

Docker Compose starts both the MariaDB database and Django web
application. The web service waits for the database to become healthy
before the Django startup process continues.

### 6. Verify the Containers

``` powershell
docker compose ps
```

The MariaDB `db` service should show as running/healthy, and the Django
`web` service should show as running.

Open the application at:

``` text
http://localhost:8000/
```

### Docker Management Commands

View Django logs:

``` powershell
docker compose logs -f web
```

View MariaDB logs:

``` powershell
docker compose logs db
```

Temporarily stop the containers:

``` powershell
docker compose stop
```

Start stopped containers again:

``` powershell
docker compose start
```

Stop and remove the containers and network:

``` powershell
docker compose down
```

`docker compose down` preserves the named MariaDB data volume.

To remove the containers **and** delete the MariaDB data volume:

``` powershell
docker compose down -v
```

Use `docker compose down -v` only when you intentionally want to delete
the Docker database data and start with a fresh database.

Docker Desktop can be closed after the containers have been stopped if
the Docker engine is no longer required.

## Optional SQLite Development

MariaDB/MySQL is the default and recommended database for this project.

SQLite may be used as a lightweight development or testing alternative
only if the Django database configuration is deliberately changed for
that environment. Production-style setup and the documented Docker
workflow use MariaDB.

## Sphinx Documentation

The Sphinx source files and generated documentation are stored in the
`docs` directory.

To rebuild the HTML documentation:

``` bash
sphinx-build -b html docs/source docs/build/html
```

The generated documentation can then be opened from:

``` text
docs/build/html/index.html
```

## Project Structure

``` text
accounts/            User accounts, registration, roles, and dashboards
api/                 REST API
articles/            Articles, newsletters, and editorial workflow
docs/                Sphinx documentation
news_project/        Django project configuration
templates/           HTML templates
Dockerfile           Docker image configuration
docker-compose.yml   Django and MariaDB container configuration
.env.example         Environment variable template
manage.py            Django management utility
requirements.txt     Python dependencies
```

## Git Branches

The project uses the following branches as part of the capstone
workflow:

-   `main` - completed working project
-   `docs` - documentation and Sphinx work
-   `container` - Docker configuration

## Testing

The project includes an automated Django test suite.

Run:

``` bash
python manage.py test
```

## Security

Passwords, database credentials, Django secret keys, API keys, and other
secrets must not be committed to this public repository.

Store sensitive configuration in the local `.env` file and keep `.env`
excluded through `.gitignore`. Commit `.env.example` only with safe
placeholder values.
