import datetime
import random
import uuid
from typing import List

from sqlalchemy import JSON, URL, Enum, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    Session,
    mapped_column,
)
from sqlalchemy_utils import create_database, database_exists

import settings
from models import DeliveryStatus

url = URL.create(
    port=3306,
    database=settings.mysql_settings.db_name,
    password=settings.mysql_settings.mysql_root_password,
    username=settings.mysql_settings.db_user,
    drivername=settings.mysql_settings.drivername,
    host=settings.mysql_settings.db_host,
)
engine = create_engine(url)


class Base(DeclarativeBase, MappedAsDataclass):
    type_annotation_map = {list[str]: JSON}


class TimeSlotORM(Base):
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime]
    supported_addresses: Mapped[list[str]] = mapped_column(
        default_factory=list,
    )
    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default_factory=lambda: str(uuid.uuid4())
    )
    __tablename__ = "time_slots"


class DeliveryORM(Base):
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus))
    slot_id: Mapped[str] = mapped_column(String(64), index=True)
    delivery_date: Mapped[datetime.date]
    user_id: Mapped[str] = mapped_column(String(64))
    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default_factory=lambda: str(uuid.uuid4())
    )
    __tablename__ = "deliveries"


if not database_exists(url):
    create_database(url)


def add_mock_slots_data(
    session: Session,
    date: datetime.date,
    supported_addresses: List[str] = [],
    max_slots: int = 8,
) -> None:
    for i in range(1, max_slots):
        slot = TimeSlotORM(
            start_time=datetime.datetime.fromisoformat(date)
            + datetime.timedelta(hours=i),
            end_time=datetime.datetime.fromisoformat(date)
            + datetime.timedelta(hours=i + 1),
            supported_addresses=supported_addresses
            or [str(random.randint(1234, 1234567))],
        )
        session.add(slot)
    session.commit()


def add_mock_data() -> None:
    dates = [
        "2022-03-16",
        str(datetime.date.today()),
        str(datetime.date.today() + datetime.timedelta(days=1)),
    ]
    with Session(engine) as session:
        if session.query(TimeSlotORM).count() != 0:
            return
        for d in dates:
            add_mock_slots_data(session=session, date=d)


Base.metadata.create_all(engine)
add_mock_data()
