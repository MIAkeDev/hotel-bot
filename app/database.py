import os
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

# <-- MODIFICAR ESTA LÍNEA
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool # Importante para Vercel + Supabase Pooler
) 
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Conversacion(Base):
    __tablename__ = "conversaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telefono = Column(String)
    idioma = Column(String)
    mensaje = Column(String)
    respuesta = Column(String)
    fue_handoff = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)

def guardar_conversacion(telefono, idioma, mensaje, respuesta, fue_handoff):
    db = SessionLocal()
    try:
        conv = Conversacion(
            telefono=telefono,
            idioma=idioma,
            mensaje=mensaje,
            respuesta=respuesta,
            fue_handoff=fue_handoff
        )
        db.add(conv)
        db.commit()
    except Exception as e:
        print(f"Error guardando conversación: {e}")
        db.rollback()
    finally:
        db.close()

def obtener_chats():
    db = SessionLocal()
    try:
        from sqlalchemy import func
        ultimos = db.query(
            Conversacion.telefono,
            func.max(Conversacion.fecha).label("ultima_fecha"),
            func.count(Conversacion.id).label("total_mensajes")
        ).group_by(Conversacion.telefono).order_by(func.max(Conversacion.fecha).desc()).all()
        return [{"telefono": r.telefono, "ultima_fecha": str(r.ultima_fecha), "total_mensajes": r.total_mensajes} for r in ultimos]
    finally:
        db.close()

def obtener_mensajes_por_telefono(telefono: str):
    db = SessionLocal()
    try:
        mensajes = db.query(Conversacion).filter(
            Conversacion.telefono == telefono
        ).order_by(Conversacion.fecha.asc()).all()
        return [
            {
                "id": m.id,
                "mensaje": m.mensaje,
                "respuesta": m.respuesta,
                "fue_handoff": m.fue_handoff,
                "idioma": m.idioma,
                "fecha": str(m.fecha)
            }
            for m in mensajes
        ]
    finally:
        db.close()

class ModoManual(Base):
    __tablename__ = "modo_manual"
    telefono = Column(String, primary_key=True)
    activo = Column(Boolean, default=True)
    fecha = Column(DateTime, default=datetime.now)

def esta_en_modo_manual(telefono: str) -> bool:
    db = SessionLocal()
    try:
        registro = db.query(ModoManual).filter(ModoManual.telefono == telefono).first()
        return registro is not None and registro.activo
    finally:
        db.close()

def activar_modo_manual(telefono: str):
    db = SessionLocal()
    try:
        registro = db.query(ModoManual).filter(ModoManual.telefono == telefono).first()
        if registro:
            registro.activo = True
        else:
            db.add(ModoManual(telefono=telefono, activo=True))
        db.commit()
    finally:
        db.close()

def desactivar_modo_manual(telefono: str):
    db = SessionLocal()
    try:
        db.query(ModoManual).filter(ModoManual.telefono == telefono).delete()
        db.commit()
    finally:
        db.close()