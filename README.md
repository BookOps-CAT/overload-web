# Overload Web

BookOps Cataloging Department browser-based toolbox.

Overload Web is a FastAPI-based web application for processing vendor MARC files, matching bib records using library APIs, and applying preconfigured order templates. The system supports form-driven input, template management, and output of structured bibliographic data with applied metadata.

## Features

- Upload and process vendor MARC files
- Match bibliographic records using matchpoints (eg. ISBN, title)
- Apply custom templates with order metadata
- Save and reuse templates
- Supports BPL and NYPL
- Web UI (Jinja2-based) and REST API interface

## Tech Stack

- **Backend Framework**: FastAPI
- **Templating Engine**: Jinja2
- **ORM**: SQLAlchemy
- **Data Models**: Pydantic
- **Containerization**: Docker

## Project Structure

overload_web/
├── application/         # Application services
├── domain/              # Domain models and business logic
├── infrastructure/      # Repositories, adapters, DB integration
├── presentation/
│   ├── api/             # API routes and Pydantic schemas
│   └── frontend/        # Jinja2 templates and page routes
├── main.py              # FastAPI application entrypoint