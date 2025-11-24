import uuid
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    Enum as PgEnum,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


# Статусы места
class SeatStatus(str, enum.Enum):
    FREE = "free"
    RESERVED = "reserved"
    SOLD = "sold"


class Seat(Base):
    __tablename__ = "seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )

    row = Column(Integer, nullable=False)
    seat_number = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    status = Column(String, default=SeatStatus.FREE.value, nullable=False)

    event = relationship("Event", back_populates="seats")
    booking = relationship("Booking", back_populates="seat", uselist=False)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seat_id = Column(
        UUID(as_uuid=True), ForeignKey("seats.id"), unique=True, nullable=False
    )

    user_identifier = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    is_paid = Column(Integer, default=0)

    seat = relationship("Seat", back_populates="booking")
