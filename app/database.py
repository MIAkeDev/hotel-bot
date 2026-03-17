import os
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
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