import concurrent
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional

import fastapi
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

import geoapify
import holidayapi
import models
import orms
import service
from models import Address, CreateDeliveryRequest, ResolveAddressRequest, TimeSlot

router = APIRouter()

logger = logging.getLogger(__name__)


async def get_session(req: Request, call_next: Any) -> Response:
    with Session(orms.engine) as session:
        session.connection(execution_options={"isolation_level": "SERIALIZABLE"})
        req.state.session = session
        return await call_next(req)


def get_session_from_request(req: Request) -> Session:
    return req.state.session


@router.post("/resolve-address")
def resolve_address(req: ResolveAddressRequest) -> Optional[Address]:
    maybe_address = geoapify.parse_address(address=req.search_term)
    if not maybe_address:
        raise fastapi.HTTPException(status_code=404, detail="Not found")
    return maybe_address


@router.post("/timeslots")
def list_time_slots(
    address: Address, session: Session = Depends(get_session_from_request)
) -> List[TimeSlot]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(holidayapi.get_holidays),
            executor.submit(service.get_time_slots, session, address),
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                logger.error("Future failed", exc_info=exc)
                raise exc
        holidays, slots = [f.result() for f in futures]
        return [s for s in slots if str(s.start_time.date()) not in holidays]


@router.get("/timeslots")
def get_all_time_slots(
    session: Session = Depends(get_session_from_request),
) -> List[TimeSlot]:
    return service.get_time_slots(session=session)


@router.post("/deliveries")
def create_delivery(
    req: CreateDeliveryRequest, session: Session = Depends(get_session_from_request)
) -> models.Delivery:
    try:
        return service.create_new_delivery(
            session=session, user_id=req.user, slot_id=req.timeslot_id
        )
    except Exception as e:
        logger.error("Failed to update delivery", exc_info=e)
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@router.post("/deliveries/{delivery_id}/cemplete")
def complete_delivery(
    delivery_id: str, session: Session = Depends(get_session_from_request)
) -> models.Delivery:
    try:
        return service.complete_delivery(session=session, delivery_id=delivery_id)
    except Exception as e:
        logger.error("Failed to update delivery", exc_info=e)
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@router.get("/deliveries/daily")
def list_daily_deliveries(
    session: Session = Depends(get_session_from_request),
) -> List[models.Delivery]:
    return service.list_deliveries(session=session, start_date=datetime.date.today())


@router.get("/deliveries/weekly")
def list_weekly_deliveries(
    session: Session = Depends(get_session_from_request),
) -> List[models.Delivery]:
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    return service.list_deliveries(session=session, start_date=start, end_date=end)


@router.delete("/deliveries/{delivery_id}")
def delete_delivery(
    delivery_id: str, session: Session = Depends(get_session_from_request)
) -> None:
    try:
        return service.delete_delivery(session=session, delivery_id=delivery_id)
    except Exception as e:
        logger.error("Failed to delete delivery", exc_info=e)
        raise fastapi.HTTPException(status_code=400, detail=str(e))
