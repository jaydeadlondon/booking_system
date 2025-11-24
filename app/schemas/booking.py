from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List


class SeatResponse(BaseModel):
    id: UUID
    row: int
    seat_number: int
    price: float
    status: str
    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: UUID
    title: str
    seats: List[SeatResponse] = []
    model_config = ConfigDict(from_attributes=True)


class BookingRequest(BaseModel):
    seat_id: UUID
    user_identifier: str


class BookingResponse(BaseModel):
    booking_id: UUID
    seat_id: UUID
    status: str
    expires_at: datetime
