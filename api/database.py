from sqlalchemy import Column, Result, String, Text, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector
from ulid import ulid
from logging import getLogger

logger = getLogger(__name__)

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:6000/postgres"

def get_engine():
    return create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=get_engine())

Base = declarative_base()
