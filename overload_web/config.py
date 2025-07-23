import os


def get_postgres_uri() -> str:
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", 5432)
    password = os.environ.get("POSTGRES_PASSWORD", "")
    user = os.environ.get("POSTGRES_USER", "overload")
    db_name = os.environ.get("POSTGRES_DB", "overload_dev")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
