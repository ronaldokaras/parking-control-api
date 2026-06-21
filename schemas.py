from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re

class VehicleCreate(BaseModel):
    plate: str
    model: str
    color: str

    @field_validator('plate')
    @classmethod
    def validate_plate(cls, v: str) -> str:
        v = v.strip().upper()
        # Padrão antigo: ABC-1234 ou ABC1234
        # Mercosul: ABC-1D23 ou ABC1D23
        pattern = r'^[A-Z]{3}-?\d[A-Z0-9]\d{2}$'
        if not re.match(pattern, v):
            raise ValueError('Placa inválida. Use formato ABC-1234 ou ABC-1D23')
        return v.replace('-', '') if len(v) == 7 else v  # normaliza sem hífen no BD se preferir

    class Config:
        from_attributes = True
        
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