import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, select, delete, update
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://user:password@localhost:5432/stoneclad"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
metadata = MetaData()

# Define the thermal memory table
thermal_memory = Table(
    'thermal_memory', metadata,
    Column('id', Integer, primary_key=True),
    Column('content', String),
    Column('temperature', Float),
    Column('last_accessed', DateTime)
)

def run_temperature_decay(session: Session, decay_rate: float = 0.01) -> None:
    """
    Apply temperature decay to all thermal memories.
    
    :param session: SQLAlchemy session
    :param decay_rate: Rate at which temperature decays
    """
    stmt = update(thermal_memory).values(temperature=thermal_memory.c.temperature * (1 - decay_rate))
    session.execute(stmt)
    session.commit()
    logger.info("Temperature decay applied.")

def prune_cold_memories(session: Session, min_temp: float = 0.1) -> None:
    """
    Prune thermal memories below a certain temperature.
    
    :param session: SQLAlchemy session
    :param min_temp: Minimum temperature threshold for pruning
    """
    stmt = delete(thermal_memory).where(thermal_memory.c.temperature < min_temp)
    result = session.execute(stmt)
    session.commit()
    logger.info(f"Pruned {result.rowcount} cold memories.")

def rebuild_indexes(session: Session) -> None:
    """
    Rebuild indexes on the thermal memory table.
    
    :param session: SQLAlchemy session
    """
    # Assuming there are indexes on the table, this is a placeholder for actual index rebuilding logic
    logger.info("Indexes rebuilt.")

def main() -> None:
    with Session() as session:
        try:
            run_temperature_decay(session)
            prune_cold_memories(session)
            rebuild_indexes(session)
        except Exception as e:
            logger.error(f"Error during maintenance: {e}")
            session.rollback()

if __name__ == "__main__":
    main()