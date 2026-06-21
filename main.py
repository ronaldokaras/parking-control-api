from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List

from database import SessionLocal, engine
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="🅿️ Parking Control - Estacionamento do Dragão")

# Templates para interface web
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================== ENDPOINTS API =====================

@app.post("/checkin", response_model=schemas.TicketResponse)
def checkin(vehicle_data: schemas.VehicleCreate, db: Session = Depends(get_db)):
    # Normaliza placa
    vehicle_data.plate = vehicle_data.plate.upper()
    
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == vehicle_data.plate).first()
    
    if not vehicle:
        vehicle = models.Vehicle(**vehicle_data.model_dump())
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

    ticket = models.ParkingTicket(vehicle_id=vehicle.id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/checkout", response_model=schemas.TicketResponse)
def checkout(plate: str, db: Session = Depends(get_db)):
    plate = plate.strip().upper()
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(404, "Veículo não encontrado")

    active_ticket = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle_id == vehicle.id,
        models.ParkingTicket.check_out.is_(None)
    ).first()

    if not active_ticket:
        raise HTTPException(404, "Veículo não está estacionado")

    now = datetime.now(timezone.utc)
    active_ticket.check_out = now
    time_diff = now - active_ticket.check_in
    total_minutes = int(time_diff.total_seconds() / 60)

    if total_minutes <= 15:
        active_ticket.total_value = 0.0
    else:
        import math
        hours = math.ceil(total_minutes / 60)
        active_ticket.total_value = hours * 5.0

    active_ticket.paid = 1
    db.commit()
    db.refresh(active_ticket)
    return active_ticket


@app.get("/parked", response_model=List[dict])  # Implementado agora!
def get_parked_vehicles(db: Session = Depends(get_db)):
    tickets = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.check_out.is_(None)
    ).all()
    
    result = []
    now = datetime.now(timezone.utc)
    for t in tickets:
        minutes = int((now - t.check_in).total_seconds() / 60)
        result.append({
            "ticket_id": t.id,
            "plate": t.vehicle.plate,
            "model": t.vehicle.model,
            "color": t.vehicle.color,
            "check_in": t.check_in,
            "minutes_parked": minutes
        })
    return result


@app.get("/history/{plate}", response_model=List[schemas.TicketResponse])
def get_history(plate: str, db: Session = Depends(get_db)):
    plate = plate.strip().upper()
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(404, "Veículo não encontrado")
    
    return db.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle_id == vehicle.id
    ).all()