import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from main import app, get_db
from database import Base
import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# --- Testes de Check-in (API) ---
def test_checkin_success(client):
    vehicle_data = {"plate": "ABC-1234", "model": "Fusca", "color": "Azul"}
    response = client.post("/api/checkin", json=vehicle_data)
    assert response.status_code == 200
    ticket = response.json()
    assert ticket["vehicle_id"] is not None
    assert ticket["check_in"] is not None
    assert ticket["check_out"] is None
    assert ticket["paid"] == 0

def test_checkin_invalid_plate(client):
    vehicle_data = {"plate": "ABC123", "model": "Fusca", "color": "Azul"}
    response = client.post("/api/checkin", json=vehicle_data)
    assert response.status_code == 422

def test_checkin_auto_uppercase(client, db_session):
    vehicle_data = {"plate": "abc-1d23", "model": "Onix", "color": "Preto"}
    response = client.post("/api/checkin", json=vehicle_data)
    assert response.status_code == 200
    ticket = response.json()
    vehicle_id = ticket["vehicle_id"]
    vehicle = db_session.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    assert vehicle.plate == "ABC-1D23"

# --- Testes de Checkout (API) ---
def test_checkout_free_grace_period(client, db_session):
    vehicle_data = {"plate": "XYZ-9876", "model": "Civic", "color": "Prata"}
    checkin_response = client.post("/api/checkin", json=vehicle_data)
    assert checkin_response.status_code == 200
    ticket_id = checkin_response.json()["id"]

    ticket = db_session.query(models.ParkingTicket).filter(models.ParkingTicket.id == ticket_id).first()
    ticket.check_in = datetime.utcnow() - timedelta(minutes=10)
    db_session.commit()

    checkout_response = client.post("/api/checkout?plate=XYZ-9876")
    assert checkout_response.status_code == 200
    data = checkout_response.json()
    assert data["total_value"] == 0.0
    assert data["paid"] == 1
    assert data["check_out"] is not None

def test_checkout_charged(client, db_session):
    vehicle_data = {"plate": "LMN-4567", "model": "Corolla", "color": "Branco"}
    client.post("/api/checkin", json=vehicle_data)

    ticket = db_session.query(models.ParkingTicket).filter(
        models.ParkingTicket.vehicle.has(plate="LMN-4567")
    ).first()
    ticket.check_in = datetime.utcnow() - timedelta(minutes=45)
    db_session.commit()

    response = client.post("/api/checkout?plate=LMN-4567")
    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == 5.0

def test_checkout_vehicle_not_found(client):
    response = client.post("/api/checkout?plate=ZZZ-0000")
    assert response.status_code == 404

def test_checkout_not_parked(client):
    vehicle_data = {"plate": "ABC-1111", "model": "Palio", "color": "Verde"}
    client.post("/api/checkin", json=vehicle_data)
    client.post("/api/checkout?plate=ABC-1111")
    response = client.post("/api/checkout?plate=ABC-1111")
    assert response.status_code == 404
    assert "não está estacionado" in response.json()["detail"]

# --- Teste do endpoint /api/parked ---
def test_parked_list(client):
    client.post("/api/checkin", json={"plate": "AAA-1111", "model": "Uno", "color": "Vermelho"})
    client.post("/api/checkin", json={"plate": "BBB-2222", "model": "Gol", "color": "Azul"})
    
    response = client.get("/api/parked")
    assert response.status_code == 200
    parked = response.json()
    assert len(parked) == 2
    
    for vehicle in parked:
        assert "ticket_id" in vehicle
        assert "plate" in vehicle
        assert "minutes_parked" in vehicle
        assert vehicle["minutes_parked"] >= 0

    client.post("/api/checkout?plate=AAA-1111")
    
    response = client.get("/api/parked")
    assert len(response.json()) == 1

# --- Teste do histórico (rota não alterada) ---
def test_history(client):
    client.post("/api/checkin", json={"plate": "HST-0001", "model": "Fit", "color": "Preto"})
    client.post("/api/checkout?plate=HST-0001")
    client.post("/api/checkin", json={"plate": "HST-0001", "model": "Fit", "color": "Preto"})
    
    response = client.get("/history/HST-0001")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["check_out"] is not None
    assert history[1]["check_out"] is None

def test_history_vehicle_not_found(client):
    response = client.get("/history/XXX-9999")
    assert response.status_code == 404