from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List

from database import SessionLocal, engine
import models
import schemas
import math

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Estacionamento")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CHECK-IN
@app.post("/checkin", response_model=schemas.TicketResponse)
def checkin(vehicle_data: schemas.VehicleCreate, db: Session = Depends(get_db)):
    vehicle_data.plate = vehicle_data.plate.upper()
    existing_vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == vehicle_data.plate).first()
    
    if existing_vehicle:
        vehicle = existing_vehicle
    else:
        vehicle = models.Vehicle(**vehicle_data.model_dump())
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

    new_ticket = models.ParkingTicket(vehicle_id=vehicle.id)
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return new_ticket

# CHECK-OUT
@app.post("/checkout", response_model=schemas.TicketResponse)
def checkout(plate: str, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    active_ticket = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle_id == vehicle.id,
        models.ParkingTicket.check_out.is_(None)
    ).first()
    
    if not active_ticket:
        raise HTTPException(status_code=404, detail="Veículo não está estacionado")
    
    now = datetime.utcnow()
    active_ticket.check_out = now
    
    time_diff = now - active_ticket.check_in
    total_minutes = int(time_diff.total_seconds() / 60)
    
    if total_minutes <= 15:
        active_ticket.total_value = 0.0
    else:        
        hours = math.ceil(total_minutes / 60)
        active_ticket.total_value = hours * 5.0
    
    active_ticket.paid = 1
    db.commit()
    db.refresh(active_ticket)
    
    return active_ticket

# HISTÓRICO
@app.get("/history/{plate}", response_model=List[schemas.TicketResponse])
def get_history(plate: str, db: Session = Depends(get_db)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    tickets = db.query(models.ParkingTicket).filter(models.ParkingTicket.vehicle_id == vehicle.id).all()
    return tickets

# LISTAR ESTACIONADOS
@app.get("/parked", response_model=List[schemas.ParkedVehicleResponse])
def get_parked_vehicles(db: Session = Depends(get_db)):
    tickets_abertos = db.query(models.ParkingTicket)\
        .options(joinedload(models.ParkingTicket.vehicle))\
        .filter(models.ParkingTicket.check_out.is_(None))\
        .all()

    now = datetime.utcnow()
    resultado = []
    for ticket in tickets_abertos:
        vehicle = ticket.vehicle
        time_parked = now - ticket.check_in
        minutes = int(time_parked.total_seconds() / 60)

        resultado.append(schemas.ParkedVehicleResponse(
            ticket_id=ticket.id,
            plate=vehicle.plate,
            model=vehicle.model,
            color=vehicle.color,
            check_in=ticket.check_in,
            minutes_parked=minutes
        ))

    return resultado