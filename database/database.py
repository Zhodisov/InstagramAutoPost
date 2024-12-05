from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.env_reader import арбуз

env_vars = арбуз()

DATABASE_URL = env_vars.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)
