from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(10), unique=True, index=True, nullable=False)
    model = Column(String(50), nullable=False)
    color = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("ParkingTicket", back_populates="vehicle")


class ParkingTicket(Base):
    __tablename__ = "parking_tickets"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    check_in = Column(DateTime, default=datetime.utcnow, nullable=False)
    check_out = Column(DateTime, nullable=True)
    total_value = Column(Float, nullable=True)
    paid = Column(Integer, default=0)

    vehicle = relationship("Vehicle", back_populates="tickets")