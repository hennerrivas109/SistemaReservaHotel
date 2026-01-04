from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Enum, Integer, Numeric, String, func

from shared.database import Base


class ReservaDB(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reserva_id = Column(String(50), unique=True, index=True)
    cliente_id = Column(String(50), index=True)
    hotel_id = Column(String(50), index=True)
    habitacion_id = Column(String(50), index=True)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    estado = Column(Enum("CREADA", "CONFIRMADA", "CANCELADA", "CHECKIN", "CHECKOUT"), default="CREADA")
    monto_total = Column(Numeric(10, 2))
    bloqueo_id = Column(String(50), nullable=True)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(DateTime, onupdate=func.now())
