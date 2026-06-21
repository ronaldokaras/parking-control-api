# 🅿️ Parking Control API – Edição Estacionamento do Dragão

**Instituto Nozes & Matemática Aplicada**  
*Departamento de Controle Veicular e Tolerância Temporal* 🚗⏱️

[![Tests](https://img.shields.io/badge/tests-10%2F10%20passed-brightgreen)](https://github.com/ronaldokaras/parking-control-api/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Uma API REST para controle de estacionamento que nasceu de uma discussão sobre **arredondamento de frações de hora** e **justiça temporal** – porque 15 minutos podem ser um presente ou uma armadilha.  
O Dragão de Óculos VR (agora também consultor de trânsito) garantiu que a regra fosse clara: **até 15 min é grátis**, depois disso, cada hora (ou fração) custa R$ 5,00.  
A Diretoria aprovou, o Juiz dormiu e o código foi escrito.

---

## 📜 Aviso do Juiz (ele acordou só para isso)

> Este sistema é uma demonstração educacional de regras de negócio e boas práticas em APIs.  
> Não use para multar veículos reais sem consultar um especialista em leis de trânsito.  
> *A matemática é exata, mas a tolerância é humana. A responsabilidade é de quem aperta Enter.*

---

## 🧙‍♂️ Lore do Estacionamento

Tudo começou quando um Membro Honorário perguntou: *“Quanto custa ficar 1h02 num estacionamento?”*  
O Dragão respondeu: *“R$ 10,00, porque arredondamos para cima.”*  
Daí surgiu a pergunta seguinte: *“E se for 14 minutos?”* – *“Grátis, porque o Juiz está com sono.”*  
E assim, a lógica virou código. Adicionamos validação de placas (padrão antigo e Mercosul), persistência em SQLite, testes com 100% de cobertura e um container Docker para rodar em qualquer lugar – inclusive no porta‑malas de um Fusca.

---

## ✨ Funcionalidades

- **Check-in** de veículos (cadastro automático se placa nova)
- **Check-out** com cálculo de valor:
  - Até 15 minutos: **grátis** 🆓
  - Acima de 15 minutos: R$ 5,00 por hora (arredondado para cima)
- **Histórico** de tickets por placa
- **Listagem de veículos estacionados** com tempo de permanência em tempo real
- **Validação de placa** (padrão antigo `ABC-1234` e Mercosul `ABC-1D23`)
- **Testes automatizados** com 100% de cobertura dos cenários principais
- **Container Docker** para execução isolada – porque o Dragão não confia em ambientes que não são reproduzíveis

---

## 🚀 Como executar localmente

### Pré‑requisitos

- Python 3.12 ou superior (o Dragão recomenda 3.12)
- (Opcional) Docker – para quem gosta de empacotar o estacionamento

### Usando Python e ambiente virtual

```bash
git clone https://github.com/ronaldokaras/parking-control-api.git
cd parking-control-api
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Acesse `http://localhost:8000/docs` para testar os endpoints no Swagger – o Dragão adora uma UI bonita.

### Usando Docker 🐳

```bash
docker build -t parking-control-api .
docker run -d -p 8000:8000 --name parking-api parking-control-api
# ou com Docker Compose:
docker-compose up -d
```

Swagger disponível em `http://localhost:8000/docs`.

---

## 🧪 Testes

```bash
pytest -v
```

Resultado: 10 testes passando – todos validados pelo Departamento de Qualidade do Instituto.

---

## 📚 Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/checkin` | Registrar entrada (body: `VehicleCreate`) |
| POST | `/checkout?plate=ABC-1234` | Registrar saída e calcular valor |
| GET | `/parked` | Listar veículos estacionados |
| GET | `/history/{plate}` | Histórico de tickets da placa |

Exemplos de requisições no Swagger UI (`/docs`).

---

## 📦 Tecnologias

- **FastAPI** – porque a velocidade importa (e o Dragão gosta de performance)
- **SQLAlchemy** – ORM que transforma tabelas em poesia
- **SQLite** – banco de dados leve, como um Fiat Uno
- **Pydantic** – validação de dados, porque placa errada dá multa
- **Pytest** – testes que pegam até os 15 minutos mais suspeitos
- **Docker** – containerização para rodar em qualquer vaga

---

## 🏛️ Veredito da Diretoria

A Diretoria do Instituto Nozes & Matemática Aplicada declara que este projeto está **aprovado por unanimidade** – o código é limpo, as regras são justas e os testes passam com honras.  
Que este estacionamento digital sirva de exemplo para todos os que desejam controlar o tempo sem perder a ternura.

---

## 📄 Licença

MIT – compartilhe o código, mas não estacione em vaga de deficiente.

---

**Instituto Nozes & Matemática Aplicada**  
*Departamento de Controle Veicular e Tolerância Temporal*  
*Quebrando cascas duras para revelar códigos com estacionamento.* 🚗🥜
```