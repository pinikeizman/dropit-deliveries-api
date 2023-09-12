import enum
from datetime import datetime
from typing import List, Optional

import pydantic


class TimeSlot(pydantic.BaseModel):
    start_time: datetime
    end_time: datetime
    supported_addresses: List[str]
    id: str

    class Config:
        from_attributes = True


class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class Delivery(pydantic.BaseModel):
    status: DeliveryStatus
    slot_id: str
    delivery_date: datetime
    user_id: str
    id: str

    class Config:
        from_attributes = True


class Address(pydantic.BaseModel):
    id: str
    address_line1: str
    address_line2: str
    country: str
    street: Optional[str] = None
    postcode: Optional[str] = None


class ResolveAddressRequest(pydantic.BaseModel):
    search_term: str = pydantic.Field(alias="searchTerm")


class CreateDeliveryRequest(pydantic.BaseModel):
    user: str
    timeslot_id: str = pydantic.Field(alias="timeslotId")
