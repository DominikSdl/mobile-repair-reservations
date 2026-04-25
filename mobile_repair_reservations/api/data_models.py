from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    phone_number: str | None = None

class ServiceCreate(BaseModel):
    price: int
    name: str

class ReservationCreate(BaseModel):
    reservation_date: str
    service_id: str
    user_id: str