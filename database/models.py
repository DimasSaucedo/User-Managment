from datetime import datetime

from database.database import Base

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean
)

from sqlalchemy.orm import relationship

from database.database import Base


class ServerList(Base):
    __tablename__ = "server_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)

    nombre = Column(String(100), nullable=False)

    descripcion = Column(String(255))

    created_at = Column(DateTime, default=datetime.now)
    
class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    list_id = Column(Integer, ForeignKey("server_lists.id"))

    nombre = Column(String(100), nullable=False)

    hostname = Column(String(255), nullable=False)

    ip = Column(String(50), nullable=False)

    puerto = Column(Integer, default=22)

    descripcion = Column(String(255))

    sistema = Column(String(20))

    activo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)

    server_list = relationship(
        "ServerList",
        back_populates="servers"
    )
    
    ultima_conexion = Column(DateTime)
    
    operations = relationship(
    "OperationItem",
    back_populates="server",
    cascade="all, delete-orphan"
    )
    
class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    ticket = Column(String(100), nullable=False)

    operador = Column(String(100), nullable=False)

    tipo = Column(String(50), nullable=False)

    estado = Column(String(50), default="PENDIENTE")

    fecha_inicio = Column(DateTime)

    fecha_fin = Column(DateTime)

    observaciones = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    items = relationship(
        "OperationItem",
        back_populates="operation",
        cascade="all, delete-orphan"
    )
    
class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    clave = Column(String(100), unique=True)

    valor = Column(Text)

    created_at = Column(DateTime, default=datetime.now)
    
class OperationItem(Base):
    __tablename__ = "operation_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    operation_id = Column(Integer, ForeignKey("operations.id"))

    server_id = Column(Integer, ForeignKey("servers.id"))

    usuario = Column(String(100), nullable=False)

    grupo = Column(String(100), nullable=False)

    tipo = Column(String(20), nullable=False)

    inicio = Column(DateTime)

    fin = Column(DateTime)

    estado = Column(String(50), default="PENDIENTE")

    mensaje = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    operation = relationship(
        "Operation",
        back_populates="items"
    )

    server = relationship(
        "Server",
        back_populates="operations"
    )

    scheduled_job = relationship(
        "ScheduledJob",
        back_populates="operation_item",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    operation_item_id = Column(
        Integer,
        ForeignKey("operation_items.id")
    )

    job_id = Column(String(100))

    fecha_programada = Column(DateTime)

    estado = Column(String(50), default="PENDIENTE")

    ultimo_resultado = Column(Text)

    created_at = Column(DateTime, default=datetime.now)

    operation_item = relationship(
        "OperationItem",
        back_populates="scheduled_job"
    )