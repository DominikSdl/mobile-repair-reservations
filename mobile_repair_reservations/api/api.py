from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from mobile_repair_reservations.core.service_handler import ServiceHandler, decode_token
from mobile_repair_reservations.core.database import get_session
from mobile_repair_reservations.core.db_models import User, Services, Reservations, Role

from mobile_repair_reservations.api.data_models import UserCreate, ServiceCreate, ReservationCreate


sh = ServiceHandler()
security = HTTPBearer()


# ======================
# AUTH
# ======================

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


def require_role(*allowed_roles: str):
    def dependency(
        current_user: User = Depends(get_current_user)
    ):
        user_roles = [role.name for role in current_user.roles]

        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not Authorized"
            )

        return current_user

    return dependency


public_router = APIRouter(prefix="/api", tags=["API"])

private_router = APIRouter(
    prefix="/api",
    tags=["API"],
    dependencies=[Depends(get_current_user)]
)

# ======================
# USERS
# ======================

@public_router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_session)):
    return sh.create_user(user_data=user_data, db_session=db)


@public_router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_session)):
    token = sh.login(email=email, password=password, db_session=db)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token}


@private_router.get("/users/{user_id}")
def read_user(
    user_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "user", "employee"))
):
    user = sh.read_user(user_id=user_id, db_session=db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = any(r.name == "admin" for r in current_user.roles)

    if str(current_user.id) != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    return user


@private_router.put("/users/{user_id}")
def update_user(
    user_id: str,
    user_data: UserCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "user"))
):
    is_admin = any(r.name == "admin" for r in current_user.roles)

    if str(current_user.id) != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        return sh.update_user(user_id=user_id, user_data=user_data, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "user"))
):
    try:
        is_admin = any(r.name == "admin" for r in current_user.roles)

        if str(current_user.id) != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        sh.delete_user(user_id=user_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.get("/users")
def list_users(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee"))
):
    return db.query(User).all()


# ======================
# SERVICES
# ======================

@private_router.post("/services", status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee"))
):
    return sh.create_service(service_data=service_data, db_session=db)


@private_router.get("/services/{service_id}")
def read_service(
    service_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee"))
):
    service = sh.read_service(service_id=service_id, db_session=db)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@private_router.put("/services/{service_id}")
def update_service(
    service_id: str,
    service_data: ServiceCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee"))
):
    try:
        return sh.update_service(service_id=service_id, service_data=service_data, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee"))
):
    try:
        sh.delete_service(service_id=service_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.get("/services")
def list_services(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "employee", "user"))
):
    return db.query(Services).all()


# ======================
# RESERVATIONS
# ======================

@private_router.post("/reservations", status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("user", "employee", "admin"))
):

    if reservation_data.user_id != str(current_user.id):

        is_admin = any(
            r.name == "admin"
            for r in current_user.roles
        )

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Cannot create reservation for another user"
            )

    existing = db.query(Reservations).filter(
        Reservations.reservation_date == reservation_data.reservation_date
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This time slot is already taken"
        )

    return sh.create_reservation(
        reservation_data=reservation_data,
        db_session=db
    )


@private_router.get("/reservations")
def list_reservations(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("user", "employee", "admin"))
):
    is_staff = any(r.name in ["admin", "employee"] for r in current_user.roles)

    if is_staff:
        return db.query(Reservations).all()
    else:
        return db.query(Reservations).filter(
            Reservations.user_id == str(current_user.id)
        ).all()


@private_router.get("/reservations/{reservation_id}")
def read_reservation(
    reservation_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("user", "employee", "admin"))
):
    reservation = sh.read_reservation(reservation_id=reservation_id, db_session=db)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    is_owner = reservation.user_id == str(current_user.id)
    is_staff = any(r.name in ["admin", "employee"] for r in current_user.roles)

    if not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="Access denied")

    return reservation


@private_router.put("/reservations/{reservation_id}")
def update_reservation(
    reservation_id: str,
    reservation_data: ReservationCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("user", "employee", "admin"))
):
    reservation = sh.read_reservation(reservation_id, db)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    is_owner = reservation.user_id == str(current_user.id)
    is_staff = any(r.name in ["admin", "employee"] for r in current_user.roles)

    if not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="Access denied")

    return sh.update_reservation(
        reservation_id=reservation_id,
        reservation_data=reservation_data,
        db_session=db,
    )


@private_router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(
    reservation_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("user", "employee", "admin"))
):
    reservation = sh.read_reservation(reservation_id, db)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    is_owner = reservation.user_id == str(current_user.id)
    is_staff = any(r.name in ["admin", "employee"] for r in current_user.roles)

    if not (is_owner or is_staff):
        raise HTTPException(status_code=403, detail="Access denied")

    sh.delete_reservation(reservation_id=reservation_id, db_session=db)

# ======================
# ROLES
# ======================

@private_router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(
    role_name: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    return sh.create_role(role_name=role_name, db_session=db)


@private_router.get("/roles")
def list_roles(
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    return db.query(Role).all()


@private_router.get("/roles/{role_name}")
def get_role(
    role_name: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    role = sh.get_role(role_name=role_name, db_session=db)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@private_router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_name: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    try:
        sh.delete_role(role_name=role_name, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.post("/users/{user_id}/roles")
def assign_role(
    user_id: str,
    role_name: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    try:
        return sh.assign_role_to_user(user_id=user_id, role_name=role_name, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.delete("/users/{user_id}/roles")
def remove_role(
    user_id: str,
    role_name: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin"))
):
    try:
        return sh.remove_role_from_user(user_id=user_id, role_name=role_name, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@private_router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(require_role("admin", "user", "employee"))
):
    is_admin = any(r.name == "admin" for r in current_user.roles)

    if str(current_user.id) != user_id and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        return sh.get_user_roles(user_id=user_id, db_session=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

