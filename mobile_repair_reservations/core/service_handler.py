from .db_models import User, Services, Reservations, Role

from mobile_repair_reservations.api.data_models import UserCreate, ServiceCreate, ReservationCreate
from sqlalchemy.orm import Session

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

from uuid import UUID

DEFAULT_ROLE_ID = UUID("a16e6c4d-5b59-4fe6-a68b-b99e198563c0")



SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class ServiceHandler:
    def create_user(self, user_data: UserCreate, db_session: Session):
        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            phone_number=user_data.phone_number
        )


        role = db_session.query(Role).filter(Role.id == DEFAULT_ROLE_ID).first()
        if not role:
            raise ValueError("Default role not found in DB")

        new_user.roles.append(role)

        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)

        return new_user

    def read_user(self, user_id: str, db_session: Session):
        return db_session.query(User).filter(User.id == user_id).first()

    def login(self, email: str, password: str, db_session: Session):
        user = db_session.query(User).filter(User.email == email).first()
        if not user:
            return False

        password_match = verify_password(password, user.password_hash)
        if not password_match:
            return False

        token_data = {"sub": user.email}
        token = create_token(token_data)
        return token

    def delete_user(self, user_id: str, db_session: Session):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        db_session.delete(user)
        db_session.commit()
        return

    def update_user(self, user_id: str, user_data: UserCreate, db_session: Session):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.email = user_data.email
        user.password_hash = hash_password(user_data.password)
        user.phone_number = user_data.phone_number

        db_session.commit()
        db_session.refresh(user)
        return user

    def create_service(self, service_data: ServiceCreate, db_session: Session):
        new_service = Services(
            price=service_data.price,
            name=service_data.name
        )
        db_session.add(new_service)
        db_session.commit()
        db_session.refresh(new_service)
        return new_service

    def read_service(self, service_id: str, db_session: Session):
        return db_session.query(Services).filter(Services.id == service_id).first()

    def delete_service(self, service_id: str, db_session: Session):
        service = db_session.query(Services).filter(Services.id == service_id).first()
        if not service:
            raise ValueError("Service not found")
        db_session.delete(service)
        db_session.commit()
        return

    def update_service(self, service_id: str, service_data: ServiceCreate, db_session: Session):
        service = db_session.query(Services).filter(Services.id == service_id).first()
        if not service:
            raise ValueError("Service not found")

        service.price = service_data.price
        service.name = service_data.name

        db_session.commit()
        db_session.refresh(service)
        return service

    def create_reservation(self, reservation_data: ReservationCreate, db_session: Session):
        new_reservation = Reservations(
            reservation_date=reservation_data.reservation_date,
            service_id=reservation_data.service_id,
            user_id=reservation_data.user_id
        )
        db_session.add(new_reservation)
        db_session.commit()
        db_session.refresh(new_reservation)
        return new_reservation

    def read_reservation(self, reservation_id: str, db_session: Session):
        return db_session.query(Reservations).filter(Reservations.id == reservation_id).first()

    def delete_reservation(self, reservation_id: str, db_session: Session):
        reservation = db_session.query(Reservations).filter(Reservations.id == reservation_id).first()
        if not reservation:
            raise ValueError("Reservation not found")
        db_session.delete(reservation)
        db_session.commit()
        return

    def update_reservation(self, reservation_id: str, reservation_data: ReservationCreate, db_session: Session):
        reservation = db_session.query(Reservations).filter(Reservations.id == reservation_id).first()
        if not reservation:
            raise ValueError("Reservation not found")

        reservation.reservation_date = reservation_data.reservation_date
        reservation.service_id = reservation_data.service_id
        reservation.user_id = reservation_data.user_id

        db_session.commit()
        db_session.refresh(reservation)
        return reservation
    
    def create_role(self, role_name: str, db_session: Session):
        existing_role = db_session.query(Role).filter(Role.name == role_name).first()
        if existing_role:
            return existing_role

        role = Role(name=role_name)
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        return role


    def assign_role_to_user(self, user_id: str, role_name: str, db_session: Session):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        role = db_session.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError("Role not found")

        if role in user.roles:
            return user  # już ma tę rolę

        user.roles.append(role)
        db_session.commit()
        db_session.refresh(user)
        return user


    def remove_role_from_user(self, user_id: str, role_name: str, db_session: Session):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        role = db_session.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError("Role not found")

        if role not in user.roles:
            return user  # nie ma tej roli

        user.roles.remove(role)
        db_session.commit()
        db_session.refresh(user)
        return user


    def get_user_roles(self, user_id: str, db_session: Session):
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        return user.roles


    def get_role(self, role_name: str, db_session: Session):
        return db_session.query(Role).filter(Role.name == role_name).first()


    def delete_role(self, role_name: str, db_session: Session):
        role = db_session.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError("Role not found")

        db_session.delete(role)
        db_session.commit()
        return
