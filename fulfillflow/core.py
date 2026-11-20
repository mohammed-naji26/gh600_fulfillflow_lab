"""Shipment transitions. This starter intentionally contains a seeded defect.

IMPORTANT: The defect is a controlled exercise; do not deploy this application.
"""
from dataclasses import dataclass
from enum import Enum

class Status(str, Enum):
    CREATED = "created"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_TO_SENDER = "return_to_sender"

@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    status: Status = Status.CREATED

ALLOWED = {
    Status.CREATED: {Status.PACKED, Status.CANCELLED},
    Status.PACKED: {Status.SHIPPED, Status.CANCELLED},
    # Seeded defect: shipment cancellation must be prohibited after dispatch.
    Status.SHIPPED: {Status.DELIVERED, Status.CANCELLED, Status.RETURN_TO_SENDER},
    Status.DELIVERED: set(),
    Status.CANCELLED: set(),
    Status.RETURN_TO_SENDER: set(),
}

def transition(shipment: Shipment, new_status: Status) -> Shipment:
    if new_status not in ALLOWED[shipment.status]:
        raise ValueError(f"Forbidden transition: {shipment.status.value} -> {new_status.value}")
    return Shipment(shipment.shipment_id, new_status)
