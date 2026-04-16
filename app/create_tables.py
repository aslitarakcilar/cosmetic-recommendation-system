from .database import Base, engine
from .models import User


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tablolar oluşturuldu ✅")


if __name__ == "__main__":
    create_tables()