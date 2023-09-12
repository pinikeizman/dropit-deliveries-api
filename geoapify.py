import logging
from functools import cache
from typing import Optional

import requests

import settings
from models import Address

logger = logging.getLogger(__name__)


def _get_search_url(address: str) -> str:
    return f"https://api.geoapify.com/v1/geocode/search?text={address}&limit=1&apiKey={settings.settings.geoapify_token}"


@cache
def parse_address(*, address: str) -> Optional[Address]:
    response = requests.get(_get_search_url(address))
    response.raise_for_status()
    maybe_features_result = next(iter(response.json().get("features", [])), None)
    if not maybe_features_result:
        return None
    return Address.model_validate(maybe_features_result.get("properties"))
