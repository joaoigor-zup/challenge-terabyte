from api.database import get_engine, Base, Memory
from sqlalchemy import text

engine = get_engine()

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS history"))
    conn.commit()

Base.metadata.create_all(bind=engine)
print("Tabela 'history' recriada com sucesso.")

#Estava dando erro na tabela por conta do history_pkey