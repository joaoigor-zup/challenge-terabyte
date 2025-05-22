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

class Memory(Base):
    __tablename__ = 'history'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid())
    content: Mapped[str] = mapped_column(Text)
    vector = mapped_column(Vector(), nullable=False)


def simples_distance_query(session: Session, query_vector: list[float], limit: int = 100, max_distance: float = 30.0) -> Result[tuple[Memory, float]]:
    distance = Memory.vector.cosine_distance(query_vector).label("distance")
    select_query = select(Memory, distance).where(distance < max_distance).order_by(distance.asc()).limit(limit)

    logger.info(f"query made: {str(select_query)}")

    return session.execute(select_query)