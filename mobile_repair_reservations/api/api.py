from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session


from mobile_repair_reservations.core.service_handler import ServiceHandler, decode_token
from mobile_repair_reservations.core.database import get_session
from mobile_repair_reservations.core.db_models import User, Services, Reservations

from mobile_repair_reservations.api.data_models import UserCreate, ServiceCreate, ReservationCreate



sh = ServiceHandler()
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


public_router = APIRouter(prefix="/api", tags=["API"])

private_router = APIRouter(
    prefix="/api",
    tags=["API"],
    dependencies=[Depends(get_current_user)]
)

# USERS

@public_router.post("/register", response_model=None, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_session)):
    return sh.create_user(user_data=user_data, db_session=db)

@public_router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_session)):
    token = sh.login(email=email, password=password, db_session=db)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token}

@private_router.get("/users/{user_id}")
def read_user(user_id: str, db: Session = Depends(get_session)):
    user = sh.read_user(user_id=user_id, db_session=db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@private_router.put("/users/{user_id}")
def update_user(user_id: str, user_data: UserCreate, db: Session = Depends(get_session)):
    try:
        return sh.update_user(user_id=user_id, user_data=user_data, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_session)):
    try:
        sh.delete_user(user_id=user_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# SERVICES

@private_router.post("/services", status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_session)):
    return sh.create_service(service_data=service_data, db_session=db)


@private_router.get("/services/{service_id}")
def read_service(service_id: str, db: Session = Depends(get_session)):
    service = sh.read_service(service_id=service_id, db_session=db)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@private_router.put("/services/{service_id}")
def update_service(service_id: str, service_data: ServiceCreate, db: Session = Depends(get_session)):
    try:
        return sh.update_service(service_id=service_id, service_data=service_data, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: str, db: Session = Depends(get_session)):
    try:
        sh.delete_service(service_id=service_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# RESERVATIONS

@private_router.post("/reservations", status_code=status.HTTP_201_CREATED)
def create_reservation(reservation_data: ReservationCreate, db: Session = Depends(get_session)):
    return sh.create_reservation(reservation_data=reservation_data, db_session=db)


@private_router.get("/reservations/{reservation_id}")
def read_reservation(reservation_id: str, db: Session = Depends(get_session)):
    reservation = sh.read_reservation(reservation_id=reservation_id, db_session=db)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@private_router.put("/reservations/{reservation_id}")
def update_reservation(
    reservation_id: str,
    reservation_data: ReservationCreate,
    db: Session = Depends(get_session),
):
    try:
        return sh.update_reservation(
            reservation_id=reservation_id,
            reservation_data=reservation_data,
            db_session=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id: str, db: Session = Depends(get_session)):
    try:
        sh.delete_reservation(reservation_id=reservation_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
