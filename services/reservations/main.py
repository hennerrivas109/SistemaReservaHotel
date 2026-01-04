from __future__ import annotations

from typing import Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.events import event_bus
from shared.security import verify_token
from shared.database import Base, engine, get_db
from services.reservations.orchestrator import CrearReservaOrchestrator
from shared.security import create_access_token
from services.reservations.schemas import CrearReservaRequest, ReservaResponse
from services.reservations.service import (
    cancel_reservation,
    checkin_reservation,
    checkout_reservation,
    create_reservation_flow,
    modify_reservation,
)
from services.reservations.repository import get_reservation
from sqlalchemy.orm import Session


app = FastAPI(title="Reservations Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/reservations")
async def create_reservation(payload: CrearReservaRequest, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> ReservaResponse:
    orch = CrearReservaOrchestrator()
    # Generar un token interno para llamadas a otros servicios
    internal_token = create_access_token({
        "usuario_id": current_user["usuario_id"],
        "username": current_user["username"],
        "rol": current_user.get("rol", "cliente"),
    })
    orchestration = await orch.crear_reserva(payload.model_dump(), token=internal_token)
    reserva = await create_reservation_flow(db, {**payload.model_dump(), **orchestration}, internal_token)
    event_bus.publicar("reserva.creada", {"cliente_id": payload.cliente_id, "hotel_id": payload.hotel_id})
    return ReservaResponse(estado="CONFIRMADA", detalles={"reserva_id": reserva.reserva_id})


@app.get("/api/v1/reservations/{reserva_id}")
def get_reservation_api(reserva_id: str, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> Dict:
    r = get_reservation(db, reserva_id)
    if not r:
        return {"error": "not_found"}
    return {
        "reserva_id": r.reserva_id,
        "cliente_id": r.cliente_id,
        "hotel_id": r.hotel_id,
        "habitacion_id": r.habitacion_id,
        "fecha_inicio": str(r.fecha_inicio),
        "fecha_fin": str(r.fecha_fin),
        "estado": r.estado,
        "monto_total": str(r.monto_total),
    }


@app.put("/api/v1/reservations/{reserva_id}")
def modify_reservation_api(reserva_id: str, payload: dict, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> Dict[str, str]:
    modify_reservation(db, reserva_id, payload)
    event_bus.publicar("reserva.modificada", {"reserva_id": reserva_id})
    return {"message": "reserva modificada"}


@app.post("/api/v1/reservations/{reserva_id}/checkin")
def checkin_api(reserva_id: str, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> Dict[str, str]:
    checkin_reservation(db, reserva_id)
    return {"message": "checkin ok"}


@app.post("/api/v1/reservations/{reserva_id}/checkout")
def checkout_api(reserva_id: str, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> Dict[str, str]:
    checkout_reservation(db, reserva_id)
    return {"message": "checkout ok"}


@app.delete("/api/v1/reservations/{reserva_id}")
async def cancel_api(reserva_id: str, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)) -> Dict[str, str]:
    internal_token = create_access_token({
        "usuario_id": current_user["usuario_id"],
        "username": current_user["username"],
        "rol": current_user.get("rol", "cliente"),
    })
    await cancel_reservation(db, reserva_id, internal_token)
    return {"message": "reserva cancelada"}


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
