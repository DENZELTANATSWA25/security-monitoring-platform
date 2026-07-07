from app.db.session import engine
from app.db.base import Base

def init_database():
    Base.metadata.create_all(bind=engine)