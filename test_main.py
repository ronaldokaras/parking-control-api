import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import models

# Importa sua aplicação e dependências
from main import app, get_db
from database import Base

# Cria um engine para banco SQLite em memória (isolado)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Pode usar :memory: também
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture que configura o banco de teste antes de cada teste
@pytest.fixture()
def db_session():
    # Cria as tabelas no banco de teste
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    # Dropa as tabelas após o teste (para próximo teste começar limpo)
    Base.metadata.drop_all(bind=engine)

# Fixture que sobrescreve a dependência get_db e fornece um cliente de teste
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
    # Limpa o override depois do teste
    app.dependency_overrides.clear()

# --- Testes de Check-in ---

def test_checkin_success(client):
    vehicle_data = {
        "plate": "ABC-1234",
        "model": "Fusca",
        "color": "Azul"
    }
    response = client.post("/checkin", json=vehicle_data)
    assert response.status_code == 200
    ticket = response.json()
    assert ticket["vehicle_id"] is not None
    assert ticket["check_in"] is not None
    assert ticket["check_out"] is None
    assert ticket["paid"] == 0

def test_checkin_invalid_plate(client):
    vehicle_data = {
        "plate": "ABC123",  # sem traço
        "model": "Fusca",
        "color": "Azul"
    }
    response = client.post("/checkin", json=vehicle_data)
    assert response.status_code == 422  # Erro de validação

def test_checkin_auto_uppercase(client, db_session):
    vehicle_data = {"plate": "abc-1d23", "model": "Onix", "color": "Preto"}
    response = client.post("/checkin", json=vehicle_data)
    assert response.status_code == 200
    ticket = response.json()
    vehicle_id = ticket["vehicle_id"]
    # Usa a sessão de teste para consultar o veículo
    vehicle = db_session.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    assert vehicle.plate == "ABC-1D23"
    

# --- Testes de Checkout ---

def test_checkout_free_grace_period(client, db_session):
    # Primeiro faz check-in manualmente (ou via endpoint)
    # Vamos usar o endpoint checkin para criar o ticket
    vehicle_data = {"plate": "XYZ-9876", "model": "Civic", "color": "Prata"}
    checkin_response = client.post("/checkin", json=vehicle_data)
    assert checkin_response.status_code == 200
    ticket_id = checkin_response.json()["id"]

    # Simula que se passaram 10 minutos (menos que 15)
    # Precisamos forçar o check_in para 10 minutos atrás, pois o endpoint usa datetime.utcnow()
    # Vamos acessar o banco de teste diretamente para alterar o ticket
    from models import ParkingTicket
    db = db_session
    ticket = db.query(ParkingTicket).filter(ParkingTicket.id == ticket_id).first()
    ticket.check_in = datetime.utcnow() - timedelta(minutes=10)
    db.commit()

    # Faz o checkout
    checkout_response = client.post("/checkout?plate=XYZ-9876")
    assert checkout_response.status_code == 200
    data = checkout_response.json()
    assert data["total_value"] == 0.0
    assert data["paid"] == 1
    assert data["check_out"] is not None

def test_checkout_charged(client, db_session):
    # Check-in
    vehicle_data = {"plate": "LMN-4567", "model": "Corolla", "color": "Branco"}
    client.post("/checkin", json=vehicle_data)

    # Altera check_in para 45 minutos atrás (1 hora cobrada, pois 45 > 15 e arredonda para cima: 1h = R$5)
    from models import ParkingTicket
    db = db_session
    ticket = db.query(ParkingTicket).filter(ParkingTicket.vehicle.has(plate="LMN-4567")).first()
    ticket.check_in = datetime.utcnow() - timedelta(minutes=45)
    db.commit()

    # Checkout
    response = client.post("/checkout?plate=LMN-4567")
    assert response.status_code == 200
    data = response.json()
    assert data["total_value"] == 5.0  # 1 hora = R$5

def test_checkout_vehicle_not_found(client):
    response = client.post("/checkout?plate=ZZZ-0000")
    assert response.status_code == 404

def test_checkout_not_parked(client):
    # Cria veículo mas sem ticket aberto? Para isso, faz check-in e checkout do mesmo veículo, depois tenta checkout de novo.
    vehicle_data = {"plate": "ABC-1111", "model": "Palio", "color": "Verde"}
    client.post("/checkin", json=vehicle_data)
    client.post("/checkout?plate=ABC-1111")  # fecha o ticket
    # Tenta checkout novamente
    response = client.post("/checkout?plate=ABC-1111")
    assert response.status_code == 404
    assert "não está estacionado" in response.json()["detail"]

# --- Teste do endpoint /parked ---

def test_parked_list(client):
    # Fazer check-in de dois carros diferentes
    client.post("/checkin", json={"plate": "AAA-1111", "model": "Uno", "color": "Vermelho"})
    client.post("/checkin", json={"plate": "BBB-2222", "model": "Gol", "color": "Azul"})
    
    # Listar estacionados
    response = client.get("/parked")
    assert response.status_code == 200
    parked = response.json()
    assert len(parked) == 2
    
    # Verifica se os campos estão presentes
    for vehicle in parked:
        assert "ticket_id" in vehicle
        assert "plate" in vehicle
        assert "minutes_parked" in vehicle
        assert vehicle["minutes_parked"] >= 0

    # Fazer checkout de um deles
    client.post("/checkout?plate=AAA-1111")
    
    # Listar novamente: deve ter apenas 1
    response = client.get("/parked")
    assert len(response.json()) == 1

# --- Teste do histórico ---

def test_history(client):
    # Cria veículo e faz dois check-ins (simular que já teve tickets anteriores)
    client.post("/checkin", json={"plate": "HST-0001", "model": "Fit", "color": "Preto"})
    client.post("/checkout?plate=HST-0001")  # fecha primeiro ticket
    
    client.post("/checkin", json={"plate": "HST-0001", "model": "Fit", "color": "Preto"})  # segundo ticket (ainda aberto)
    
    response = client.get("/history/HST-0001")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2  # dois tickets
    # O primeiro deve ter check_out preenchido, o segundo não
    assert history[0]["check_out"] is not None
    assert history[1]["check_out"] is None

def test_history_vehicle_not_found(client):
    response = client.get("/history/XXX-9999")
    assert response.status_code == 404