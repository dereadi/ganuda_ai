from typing import List, Dict, Optional
from ganuda.backend.models import Hardware, InventoryRecord
from ganuda.backend.db import get_db_session


def add_hardware_to_inventory(hardware: Hardware) -> None:
    """
    Adds a new hardware item to the inventory.
    """
    with get_db_session() as session:
        session.add(hardware)
        session.commit()


def update_hardware_in_inventory(hardware_id: int, updates: Dict[str, any]) -> Optional[Hardware]:
    """
    Updates an existing hardware item in the inventory.
    """
    with get_db_session() as session:
        hardware = session.query(Hardware).filter_by(id=hardware_id).first()
        if hardware:
            for key, value in updates.items():
                setattr(hardware, key, value)
            session.commit()
            return hardware
        return None


def remove_hardware_from_inventory(hardware_id: int) -> bool:
    """
    Removes a hardware item from the inventory.
    """
    with get_db_session() as session:
        hardware = session.query(Hardware).filter_by(id=hardware_id).first()
        if hardware:
            session.delete(hardware)
            session.commit()
            return True
        return False


def list_hardware_in_inventory() -> List[Hardware]:
    """
    Lists all hardware items in the inventory.
    """
    with get_db_session() as session:
        return session.query(Hardware).all()


def search_hardware_in_inventory(query: str) -> List[Hardware]:
    """
    Searches for hardware items in the inventory based on a query.
    """
    with get_db_session() as session:
        return session.query(Hardware).filter(
            (Hardware.name.like(f'%{query}%')) |
            (Hardware.serial_number.like(f'%{query}%'))
        ).all()


def create_inventory_record(hardware_id: int, record: InventoryRecord) -> None:
    """
    Creates a new inventory record for a specific hardware item.
    """
    with get_db_session() as session:
        hardware = session.query(Hardware).filter_by(id=hardware_id).first()
        if hardware:
            hardware.inventory_records.append(record)
            session.commit()


def list_inventory_records_for_hardware(hardware_id: int) -> List[InventoryRecord]:
    """
    Lists all inventory records for a specific hardware item.
    """
    with get_db_session() as session:
        hardware = session.query(Hardware).filter_by(id=hardware_id).first()
        if hardware:
            return hardware.inventory_records
        return []