from fastapi import FastAPI

app = FastAPI(title="Sistema de Estacionamento")

@app.get("/")
def root():
    return {"message": "API do Estacionamento está no ar!"}