# Use a lightweight official Python image as the base image.
FROM python:3.12-slim

# Prevent Python from creating .pyc files inside the container.
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure Python output is sent directly to the terminal.
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container.
WORKDIR /app

# Install Linux packages required to build and use mysqlclient.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency file first to improve Docker layer caching.
COPY requirements.txt .

# Install the Python project dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project into the container.
COPY . .

# Document the port used by the Django application.
EXPOSE 8000

# Start the Django development server.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]