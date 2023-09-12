import datetime
from typing import Iterator

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import exceptions
import models
import orms
import service
from main import app
from orms import add_mock_slots_data

client = TestClient(app)


#
# @pytest.fixture
# def db() -> Iterator[Mysqld]:
#     with Mysqld() as mysqld:
#         yield mysqld
#


@pytest.fixture
def db_session() -> Iterator[Session]:
    with Session(sqlalchemy.create_engine("sqlite://")) as session:
        orms.Base.metadata.create_all(session.bind)
        yield session


def test_create_delivery_should_not_create_delivery_if_day_has_10_deliveries(
    db_session: Session,
):
    add_mock_slots_data(
        session=db_session,
        date=str(datetime.date.today()),
        supported_addresses=["1234"],
        max_slots=12,
    )
    slots_orms = db_session.query(orms.TimeSlotORM).all()
    slots = service.get_time_slots(
        session=db_session,
        address=models.Address(
            address_line1="test1",
            address_line2="test2",
            country="IL",
            street="test",
            postcode="1234",
        ),
    )
    assert len(slots) == len(slots_orms)
    with pytest.raises(exceptions.DeliveryDayFullException):
        for s in slots:
            service.create_new_delivery(
                session=db_session, user_id="test_user", slot_id=s.id
            )
    assert db_session.query(orms.DeliveryORM).count() == 10


def test_create_delivery_should_not_create_delivery_if_slot_has_2_deliveries(
    db_session: Session,
):
    add_mock_slots_data(
        session=db_session,
        date=str(datetime.date.today()),
        supported_addresses=["1234"],
        max_slots=2,
    )
    slots_orms = db_session.query(orms.TimeSlotORM).all()
    service.create_new_delivery(
        session=db_session, user_id="test_user", slot_id=slots_orms[0].id
    )
    service.create_new_delivery(
        session=db_session, user_id="test_user", slot_id=slots_orms[0].id
    )
    with pytest.raises(exceptions.SlotFullException):
        service.create_new_delivery(
            session=db_session, user_id="test_user", slot_id=slots_orms[0].id
        )
    assert db_session.query(orms.DeliveryORM).count() == 2
