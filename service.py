import datetime
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

import exceptions
import models
import orms
from models import Address, Delivery, DeliveryStatus, TimeSlot
from orms import TimeSlotORM


def get_time_slots(
    session: Session, address: Optional[Address] = None
) -> List[TimeSlot]:
    q = session.query(TimeSlotORM)
    if address:
        q = q.filter(TimeSlotORM.supported_addresses.contains(address.postcode))
    return [TimeSlot.model_validate(ts) for ts in q.all()]


def create_new_delivery(session: Session, slot_id: str, user_id: str) -> Delivery:
    slot_orm = session.query(orms.TimeSlotORM).filter_by(id=slot_id).one_or_none()
    if not slot_orm:
        raise exceptions.NotFoundException(f"Slot with id {slot_id} not found")
    delivery_orm = orms.DeliveryORM(
        status=DeliveryStatus.PENDING,
        delivery_date=slot_orm.start_time,
        slot_id=slot_id,
        user_id=user_id,
    )
    session.add(delivery_orm)
    session.flush()
    if session.query(orms.DeliveryORM).filter_by(slot_id=slot_orm.id).count() > 2:
        session.rollback()
        raise exceptions.SlotFullException(f"Slot with id {slot_orm.id} is full")
    if (
        session.query(orms.DeliveryORM)
        .filter_by(delivery_date=delivery_orm.delivery_date.date())
        .count()
        > 10
    ):
        session.rollback()
        raise exceptions.DeliveryDayFullException(
            f"Delivery day {delivery_orm.delivery_date} is full"
        )
    session.commit()
    return Delivery.model_validate(delivery_orm)


def complete_delivery(session: Session, delivery_id: str) -> Delivery:
    delivery_orm = (
        session.query(orms.DeliveryORM)
        .filter_by(id=delivery_id, status=DeliveryStatus.PENDING)
        .one_or_none()
    )
    if not delivery_orm:
        raise exceptions.NotFoundException(
            f"Delivery with id {delivery_id} and status {DeliveryStatus.PENDING} not found"
        )
    delivery_orm.status = DeliveryStatus.COMPLETED
    session.commit()
    return Delivery.model_validate(delivery_orm)


def delete_delivery(session: Session, delivery_id: str) -> None:
    session.query(orms.DeliveryORM).filter_by(id=delivery_id).delete()
    session.commit()


def list_deliveries(
    session: Session,
    start_date: datetime.date,
    end_date: Optional[datetime.date] = None,
) -> List[models.Delivery]:
    q = session.query(orms.DeliveryORM)
    if start_date and end_date:
        q = q.filter(
            and_(
                orms.DeliveryORM.delivery_date >= start_date,
                orms.DeliveryORM.delivery_date <= end_date,
            )
        )
    else:
        q = q.filter(orms.DeliveryORM.delivery_date == start_date)
    return [Delivery.model_validate(d) for d in q.all()]
