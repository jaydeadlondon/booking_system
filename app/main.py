from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(title="Booking System HighLoad")

app.include_router(endpoints.router, prefix="/api")
