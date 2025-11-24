import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, delete
from datetime import datetime
from app.models.ticket import Booking, Seat, SeatStatus
from app.services.booking_service import invalidate_cache


async def _cleanup_logic():
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        stmt = (
            select(Booking).where(Booking.expires_at < now).where(Booking.is_paid == 0)
        )
        result = await db.execute(stmt)
        expired_bookings = result.scalars().all()

        if not expired_bookings:
            return "No expired bookings"

        deleted_count = 0
        for booking in expired_bookings:
            seat_stmt = select(Seat).where(Seat.id == booking.seat_id)
            res = await db.execute(seat_stmt)
            seat = res.scalars().first()

            if seat:
                seat.status = SeatStatus.FREE.value
                seat.booking = None
                db.add(seat)

                await invalidate_cache(str(seat.event_id))

            await db.delete(booking)
            deleted_count += 1

        await db.commit()
        return f"Cleaned up {deleted_count} bookings"


@celery_app.task
def cleanup_bookings():
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_cleanup_logic())
