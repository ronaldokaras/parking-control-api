from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import re

class VehicleCreate(BaseModel):
    plate: str = Field(
        ...,
        min_length=7,
        max_length=8,
        pattern=r'^[A-Za-z]{3}-(?:[0-9]{4}|[0-9][A-Za-z][0-9]{2})$',
        description="Placa no formato AAA-1234 ou AAA-1B23"
    )
    model: str
    color: str


class VehicleResponse(BaseModel):
    id: int
    plate: str
    model: str
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}

class TicketCreate(BaseModel):
    plate: str

class TicketCheckout(BaseModel):
    plate: str

class TicketResponse(BaseModel):
    id: int
    vehicle_id: int
    check_in: datetime
    check_out: Optional[datetime]
    total_value: Optional[float]
    paid: int

    model_config = {"from_attributes": True}
class ParkedVehicleResponse(BaseModel):
    ticket_id: int
    plate: str
    model: str
    color: str
    check_in: datetime
    minutes_parked: int

    model_config = {"from_attributes": True}