from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

class Database:
    def __init__(self, config):
        self.engine = create_engine(config['database_url'])
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Initialize the database by creating all tables"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        """Get a new database session"""
        return self.Session()