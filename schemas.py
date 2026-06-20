from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VehicleCreate(BaseModel):
    plate: str
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