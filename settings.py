import logging

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = False
    env: str = "local"
    geoapify_token: str
    holiday_api_token: str
    model_config = SettingsConfigDict(env_file=".env", extra=pydantic.Extra.allow)


class MySqlSetting(Settings):
    mysql_root_password: str = "test"
    db_name: str = "dropit"
    db_port: str = "3306"
    db_host: str = "database"
    db_user: str = "root"
    drivername: str = "mysql"


settings = Settings()
mysql_settings = MySqlSetting()


if settings.debug:
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
