import logging
from functools import cache
from typing import List

import requests

import settings

logger = logging.getLogger(__name__)


@cache
def get_holidays(*, country: str = "IL", year: str = "2022") -> List[str]:
    url = f"https://holidayapi.com/v1/holidays?key={settings.settings.holiday_api_token}&country={country}&year={year}"
    response = requests.get(url)
    response.raise_for_status()
    return [h.get("date") for h in response.json().get("holidays", [])]
