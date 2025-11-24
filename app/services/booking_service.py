from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.models.ticket import Seat, Booking, SeatStatus
from app.schemas.booking import BookingRequest
import json
import redis.asyncio as redis
from app.core.config import settings
import asyncio

BOOKING_TTL_MINUTES = 10
redis_client = redis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)


async def create_booking_safe(db: AsyncSession, request: BookingRequest):
    async with db.begin():
        stmt = select(Seat).where(Seat.id == request.seat_id).with_for_update()
        result = await db.execute(stmt)
        seat = result.scalars().first()

        if not seat:
            raise HTTPException(404, "Seat not found")

        if seat.status != SeatStatus.FREE.value:
            raise HTTPException(409, "Seat is already taken")

        expires_at = datetime.utcnow() + timedelta(minutes=BOOKING_TTL_MINUTES)
        new_booking = Booking(
            seat_id=seat.id,
            user_identifier=request.user_identifier,
            expires_at=expires_at,
        )
        db.add(new_booking)

        seat.status = SeatStatus.RESERVED.value
        db.add(seat)

    await invalidate_cache(str(seat.event_id))
    return new_booking


async def get_cached_seats(event_id: str):
    cache_key = f"event_seats:{event_id}"
    data = await redis_client.get(cache_key)
    if data:
        return json.loads(data)
    return None


async def set_cached_seats(event_id: str, seats_data: list):
    cache_key = f"event_seats:{event_id}"
    await redis_client.set(cache_key, json.dumps(seats_data), ex=60)


async def invalidate_cache(event_id: str):
    cache_key = f"event_seats:{event_id}"
    await redis_client.delete(cache_key)


async def process_payment(booking_id: str, db: AsyncSession):
    async with db.begin():
        stmt = select(Booking).where(Booking.id == booking_id).with_for_update()
        result = await db.execute(stmt)
        booking = result.scalars().first()

        if not booking:
            raise HTTPException(404, "Booking not found")

        if booking.is_paid:
            raise HTTPException(400, "Already paid")
        
        if datetime.utcnow() > booking.expires_at:
            raise HTTPException(400, "Booking expired")

        await asyncio.sleep(2) 

        booking.is_paid = 1
        
        seat_stmt = select(Seat).where(Seat.id == booking.seat_id)
        res = await db.execute(seat_stmt)
        seat = res.scalars().first()
        if seat:
            seat.status = SeatStatus.SOLD.value
            db.add(seat)

            await invalidate_cache(str(seat.event_id))
            
        db.add(booking)
        
    return {"status": "paid", "booking_id": booking_id}