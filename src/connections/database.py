from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config.settings import settings

connect_args = {}
if settings.SSL_ROOT_CERT:
    connect_args = {
        "sslmode": settings.SSL_MODE,
        "sslrootcert": settings.SSL_ROOT_CERT
    }

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()