from pydantic import SecretStr

from app.core.config import Settings, get_settings


def test_database_url_is_not_exposed_in_repr() -> None:
    assert "test:test" not in repr(get_settings())


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = Settings(
        database_url=SecretStr("postgresql+psycopg://u:p@localhost/db"),
        cors_origins="http://a.test, http://b.test ,",
    )
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]
