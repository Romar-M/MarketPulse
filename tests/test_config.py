from src.config import Settings


def test_default_values():
    s = Settings()
    assert s.threshold == 0.01
    assert s.window_minutes == 60


def test_database_url_format():
    s = Settings(db_user="tester", db_pass="secret", db_host="db", db_name="testdb")
    expected = "postgresql+asyncpg://tester:secret@db:5432/testdb"
    assert s.database_url == expected
