from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader   
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import List
import math

from database import SessionLocal, engine
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="🅿️ Parking Control - Estacionamento do Dragão",
    description="Sistema profissional de controle de estacionamento",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Environment(loader=FileSystemLoader("templates"))  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===================== PÁGINA INICIAL =====================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    template = templates.get_template("index.html")
    return HTMLResponse(template.render({"request": request}))


# ===================== ENDPOINTS PARA INTERFACE HTMX =====================
@app.post("/checkin", response_class=HTMLResponse)
def checkin_htmx(
    request: Request,
    plate: str = Form(...),
    model: str = Form(...),
    color: str = Form(...),
    db: Session = Depends(get_db)
):
    plate = plate.strip().upper()
    
    # Validação básica (pode ser melhorada depois)
    if not plate:
        return '<div class="bg-red-900 border border-red-500 text-red-300 px-6 py-4 rounded-2xl">❌ Placa inválida.</div>'
    
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    
    if not vehicle:
        vehicle = models.Vehicle(plate=plate, model=model, color=color)
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

    ticket = models.ParkingTicket(vehicle_id=vehicle.id)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return f"""
    <div class="alert alert-success">
        ✅ <strong>Check-in realizado com sucesso!</strong><br>
        Placa: <strong>{plate}</strong> | {model} - {color}
    </div>
    """


@app.post("/checkout", response_class=HTMLResponse)
def checkout_htmx(
    request: Request,
    plate: str = Form(...),
    db: Session = Depends(get_db)
):
    plate = plate.strip().upper()
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    
    if not vehicle:
        return f"""
        <div class="alert alert-error">❌ Placa inválida.
        </div>
        """

    active_ticket = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle_id == vehicle.id,
        models.ParkingTicket.check_out.is_(None)
    ).first()

    if not active_ticket:
        return f"""
        <div class="alert alert-warning">
            ⚠️ O veículo <strong>{plate}</strong> não está estacionado no momento.
        </div>
        """

    now = datetime.utcnow()
    active_ticket.check_out = now
    time_diff = now - active_ticket.check_in
    total_minutes = int(time_diff.total_seconds() / 60)

    if total_minutes <= 15:
        active_ticket.total_value = 0.0
        message = "Grátis (até 15 minutos)"
    else:
        hours = math.ceil(total_minutes / 60)
        active_ticket.total_value = hours * 5.0
        message = f"R$ {active_ticket.total_value:.2f} ({hours}h)"

    active_ticket.paid = 1
    db.commit()
    db.refresh(active_ticket)

    return f"""
    <div class="alert alert-success">
        💰 <strong>Check-out realizado!</strong><br>
        Placa: <strong>{plate}</strong><br>
        Tempo: {total_minutes} minutos<br>
        Valor: <strong>{message}</strong>
    </div>
    """


@app.get("/parked-html", response_class=HTMLResponse)
def get_parked_vehicles_html(db: Session = Depends(get_db)):
    tickets = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.check_out.is_(None)
    ).all()
    
    now = datetime.utcnow()
    html = ""
    
    if not tickets:
        return '<div class="text-slate-400 text-center py-8">Nenhum veículo estacionado no momento.</div>'
    
    for t in tickets:
        minutes = int((now - t.check_in).total_seconds() / 60)
        html += f"""
        <div class="parked-card">
            <div>
                <div class="parked-plate">{t.vehicle.plate}</div>
                <div class="parked-model">{t.vehicle.model} • {t.vehicle.color}</div>
            </div>
            <div class="parked-time">{minutes} min</div>
            <div class="parked-date">
                Entrada: {t.check_in.strftime("%d/%m/%Y %H:%M")}
            </div>
        </div>
        """
    return html


# ===================== API REST (JSON) PARA TESTES E INTEGRAÇÃO =====================
@app.post("/api/checkin", response_model=schemas.TicketResponse)
def checkin_api(vehicle_data: schemas.VehicleCreate, db: Session = Depends(get_db)):
    # Converter placa para maiúsculo
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


@app.post("/api/checkout", response_model=schemas.TicketResponse)
def checkout_api(plate: str, db: Session = Depends(get_db)):
    plate = plate.strip().upper()
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


@app.get("/api/parked", response_model=List[schemas.ParkedVehicleResponse])
def get_parked_vehicles_api(db: Session = Depends(get_db)):
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


@app.get("/history/{plate}", response_model=List[schemas.TicketResponse])
def get_history(plate: str, db: Session = Depends(get_db)):
    plate = plate.strip().upper()
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.plate == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    tickets = db.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle_id == vehicle.id
    ).all()
    return tickets