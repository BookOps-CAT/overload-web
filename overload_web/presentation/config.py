from pydantic_settings import BaseSettings, SettingsConfigDict


class OverloadSettings(BaseSettings):
    """
    Settings for the Overload Web application.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    app_name: str = "Overload Web"
