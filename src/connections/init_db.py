from src.connections.database import engine, Base
from src.domain.models import Department, Job, HiredEmployee

def create_tables():
    print("Creating Tables...")
    Base.metadata.create_all(bind=engine)
    print("¡Tables created sussesfully!")

if __name__ == "__main__":
    create_tables()