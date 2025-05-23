from sqlalchemy import Column, Result, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from pgvector.sqlalchemy import Vector
from ulid import ulid
from logging import getLogger

from api.database import Base

logger = getLogger(__name__)

class HistoryEntity(Base):
    __tablename__ = 'history'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=ulid())
    content: Mapped[str] = mapped_column(Text)
    vector = mapped_column(Vector(), nullable=False)

class HistoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, content:str, vector: list[float]) -> HistoryEntity:
        _history = HistoryEntity(id = ulid(), 
                                 content = content, 
                                 vector = vector
        )
        try:
            self.session.add(_history)
            self.session.commit()
            self.session.refresh(_history)
        except Exception as ex:
            logger.warning(f"Fail to save {ex}")
            self.session.rollback()

    
    def simple_distance_query(self, query_vector: list[float], limit: int = 100, max_distance: float = 0.6) -> Result[tuple[HistoryEntity, float]]:
        distance = HistoryEntity.vector.cosine_distance(query_vector).label("distance")
        select_query = select(HistoryEntity, distance).where(distance < max_distance).order_by(distance.asc()).limit(limit)

        logger.info(f"query made: {str(select_query)}")

        return self.session.execute(select_query)