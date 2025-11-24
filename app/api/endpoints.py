from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.event import Event
from app.models.ticket import Seat, SeatStatus
from app.schemas.booking import (
    EventResponse,
    BookingRequest,
    BookingResponse,
    SeatResponse,
)
from app.services.booking_service import (
    create_booking_safe,
    get_cached_seats,
    set_cached_seats,
)
from datetime import datetime, timedelta
from app.services.booking_service import process_payment

router = APIRouter()


@router.post("/init_db")
async def init_database(db: AsyncSession = Depends(get_db)):
    event = Event(
        title="Eminem Live Concert",
        description="World Tour 2025",
        start_time=datetime.utcnow() + timedelta(days=30),
    )
    db.add(event)
    await db.flush()

    seats = []
    for row in range(1, 6):
        for number in range(1, 11):
            seats.append(
                Seat(
                    event_id=event.id,
                    row=row,
                    seat_number=number,
                    price=100.0,
                    status=SeatStatus.FREE.value,
                )
            )

    db.add_all(seats)
    await db.commit()

    return {"message": f"Created event '{event.title}' with {len(seats)} seats"}


@router.get("/events", response_model=list[EventResponse])
async def get_events(db: AsyncSession = Depends(get_db)):
    stmt = select(Event).options(selectinload(Event.seats))
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/book/safe", response_model=BookingResponse)
async def book_seat_safe(request: BookingRequest, db: AsyncSession = Depends(get_db)):
    booking = await create_booking_safe(db, request)

    return BookingResponse(
        booking_id=booking.id,
        seat_id=booking.seat_id,
        status="created",
        expires_at=booking.expires_at,
    )


@router.get("/events/{event_id}/seats", response_model=list[SeatResponse])
async def get_event_seats(event_id: str, db: AsyncSession = Depends(get_db)):
    cached = await get_cached_seats(event_id)
    if cached:
        return cached

    stmt = (
        select(Seat)
        .where(Seat.event_id == event_id)
        .order_by(Seat.row, Seat.seat_number)
    )
    result = await db.execute(stmt)
    seats = result.scalars().all()

    seats_data = [SeatResponse.model_validate(s).model_dump(mode="json") for s in seats]

    await set_cached_seats(event_id, seats_data)

    return seats


@router.post("/bookings/{booking_id}/pay")
async def pay_for_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db)
):
    return await process_payment(booking_id, db)