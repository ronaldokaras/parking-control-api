from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import re

class VehicleCreate(BaseModel):
    plate: str = Field(
        ...,
        min_length=7,
        max_length=8,
        pattern=r'^[A-Z]{3}-(?:[0-9]{4}|[0-9][A-Z][0-9]{2})$',
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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True