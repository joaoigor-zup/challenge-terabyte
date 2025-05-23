from sqlalchemy import Column, Result, String, Text, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector
from ulid import ulid
from logging import getLogger
import os

logger = getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:6000/postgres")

def get_engine():
    return create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# Manter a classe Memory existente para compatibilidade
class Memory(Base):
    __tablename__ = 'history'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(ulid()))
    content: Mapped[str] = mapped_column(Text)
    vector = mapped_column(Vector(3072), nullable=False)

def create_tables():
    """Cria todas as tabelas do banco de dados."""
    try:
        # Importar modelos aqui para evitar circular import
        from api.models import Conversation, Message
        
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

def get_db():
    """Dependency para obter sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def simple_distance_query(session: Session, query_vector: list[float], limit: int = 100, max_distance: float = 0.5):
    """
    Busca por similaridade usando distância coseno.
    
    Args:
        session: Sessão do SQLAlchemy
        query_vector: Vetor de busca
        limit: Limite de resultados
        max_distance: Distância máxima (0.0 = idêntico, 1.0 = completamente diferente)
    """
    from api.models import Message  # Import tardio para evitar circular import
    
    try:
        distance = Message.embedding.cosine_distance(query_vector).label("distance")
        select_query = select(Message, distance).where(
            Message.embedding.isnot(None)
        ).where(
            distance < max_distance
        ).order_by(distance.asc()).limit(limit)

        logger.info(f"Executando busca por similaridade com {len(query_vector)} dimensões")

        return session.execute(select_query)
    except Exception as e:
        logger.error(f"Erro na busca por similaridade: {e}")
        return []

def test_db_connection():
    """Testa a conexão com o banco de dados."""
    try:
        with SessionLocal() as session:
            result = session.execute(select(1))
            logger.info("Conexão com banco de dados OK")
            return True
    except Exception as e:
        logger.error(f"Erro na conexão com banco: {e}")
        return False