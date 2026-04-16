from sqlalchemy import text

from .database import engine


def test_connection():
    print("SQLite bağlantısı test ediliyor...")

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Bağlantı başarılı ✅")
        print("Sonuç:", result.scalar())


if __name__ == "__main__":
    test_connection()