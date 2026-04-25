from fastapi import FastAPI
from mobile_repair_reservations.api.api import public_router, private_router


app = FastAPI()
app.include_router(public_router)
app.include_router(private_router)