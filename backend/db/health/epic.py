# /ganuda/backend/db/health/epic.py

from typing import List, Dict, Optional
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()
logger = logging.getLogger(__name__)

class Node(Base):
    __tablename__ = 'nodes'
    
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(50), unique=True, nullable=False)
    ip_address: str = Column(String(15), nullable=False)
    status: str = Column(String(20), nullable=False)
    load: float = Column(Float, nullable=False)
    last_updated: datetime = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Node(name={self.name}, ip_address={self.ip_address}, status={self.status}, load={self.load})>"

class ThermalMemory(Base):
    __tablename__ = 'thermal_memory'
    
    id: int = Column(Integer, primary_key=True)
    node_id: int = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    temperature: float = Column(Float, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)
    data: str = Column(String(1000), nullable=False)

    node = relationship("Node", back_populates="thermal_memory")

    def __repr__(self) -> str:
        return f"<ThermalMemory(node_id={self.node_id}, temperature={self.temperature}, timestamp={self.timestamp})>"

Node.thermal_memory = relationship("ThermalMemory", order_by=ThermalMemory.timestamp, back_populates="node")

class DBHealthEpic:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_node(self, name: str, ip_address: str, status: str, load: float) -> None:
        session = self.Session()
        node = Node(name=name, ip_address=ip_address, status=status, load=load)
        session.add(node)
        session.commit()
        logger.info(f"Node {name} added to the database.")
        session.close()

    def update_node(self, node_id: int, status: str, load: float) -> None:
        session = self.Session()
        node = session.query(Node).filter_by(id=node_id).first()
        if node:
            node.status = status
            node.load = load
            node.last_updated = datetime.utcnow()
            session.commit()
            logger.info(f"Node {node.id} updated: status={status}, load={load}")
        else:
            logger.error(f"Node {node_id} not found.")
        session.close()

    def add_thermal_memory(self, node_id: int, temperature: float, data: str) -> None:
        session = self.Session()
        thermal_memory = ThermalMemory(node_id=node_id, temperature=temperature, data=data)
        session.add(thermal_memory)
        session.commit()
        logger.info(f"Thermal memory added for node {node_id}: temperature={temperature}")
        session.close()

    def get_nodes(self) -> List[Node]:
        session = self.Session()
        nodes = session.query(Node).all()
        session.close()
        return nodes

    def get_thermal_memory(self, node_id: int) -> List[ThermalMemory]:
        session = self.Session()
        thermal_memory = session.query(ThermalMemory).filter_by(node_id=node_id).all()
        session.close()
        return thermal_memory

    def prune_cold_memories(self, threshold: float) -> None:
        session = self.Session()
        cold_memories = session.query(ThermalMemory).filter(ThermalMemory.temperature < threshold).all()
        for memory in cold_memories:
            session.delete(memory)
            logger.info(f"Pruned cold memory for node {memory.node_id}: temperature={memory.temperature}")
        session.commit()
        session.close()

    def rebuild_indexes(self) -> None:
        session = self.Session()
        session.execute("REINDEX TABLE nodes")
        session.execute("REINDEX TABLE thermal_memory")
        session.commit()
        logger.info("Indexes rebuilt for nodes and thermal_memory tables.")
        session.close()

if __name__ == "__main__":
    db_url = "sqlite:///stoneclad.db"
    db_health = DBHealthEpic(db_url)
    
    # Example usage
    db_health.add_node(name="Redfin", ip_address="192.168.1.10", status="healthy", load=0.01)
    db_health.add_node(name="Owlfin", ip_address="192.168.1.11", status="healthy", load=0.06)
    db_health.add_node(name="Eaglefin", ip_address="192.168.1.12", status="healthy", load=0.06)
    db_health.add_node(name="Bluefin", ip_address="192.168.1.13", status="healthy", load=0.65)
    
    db_health.add_thermal_memory(node_id=1, temperature=59.0, data="GPU at rest")
    db_health.add_thermal_memory(node_id=2, temperature=36.4, data="Lightweight monitoring")
    db_health.add_thermal_memory(node_id=3, temperature=36.4, data="Lightweight monitoring")
    db_health.add_thermal_memory(node_id=4, temperature=36.4, data="DB operations")
    
    nodes = db_health.get_nodes()
    for node in nodes:
        print(node)
    
    thermal_memory = db_health.get_thermal_memory(node_id=1)
    for memory in thermal_memory:
        print(memory)
    
    db_health.prune_cold_memories(threshold=35.0)
    db_health.rebuild_indexes()