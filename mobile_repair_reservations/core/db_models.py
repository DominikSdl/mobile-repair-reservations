from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class UserRoleMapping(Base):
    __tablename__ = "user_role_mapping"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    users = relationship(
        "User",
        secondary="user_role_mapping",
        back_populates="roles"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)

    roles = relationship(
        "Role",
        secondary="user_role_mapping",
        back_populates="users"
    )


class Services(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    price = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

    reservations = relationship("Reservations", back_populates="service")


class Reservations(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    reservation_date = Column(String, nullable=False)

    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    service = relationship("Services", back_populates="reservations")
    user = relationship("User")
