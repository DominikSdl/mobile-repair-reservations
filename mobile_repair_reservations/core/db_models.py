from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Integer, String, Column, ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)

class Services(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    price = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

class Reservations(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    reservation_date = Column(String, nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)