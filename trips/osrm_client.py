"""
Cliente OSRM para obtener distancia y duración de rutas por carretera.
Utiliza el demo server público de OSRM (gratis, sin API key).
Implementa caché local para no repetir llamadas.
"""

import logging
from functools import lru_cache

import requests

from .ecuador_locations import get_coordinates

logger = logging.getLogger(__name__)

OSRM_BASE_URL = "https://router.project-osrm.org"


@lru_cache(maxsize=500)
def _osrm_route_cached(key):
    lon1, lat1, lon2, lat2 = key
    url = f"{OSRM_BASE_URL}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    try:
        response = requests.get(url, params={"overview": "false"}, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            return None, None
        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60
        return round(distance_km, 1), round(duration_min)
    except requests.RequestException as e:
        logger.warning(f"OSRM error para {key}: {e}")
        return None, None


def get_route_info(origin_city, destination_city):
    lat1, lon1 = get_coordinates(origin_city)
    lat2, lon2 = get_coordinates(destination_city)

    if lat1 is None or lat2 is None:
        return None, None

    if origin_city == destination_city:
        return 0.0, 0.0

    return _osrm_route_cached((lon1, lat1, lon2, lat2))
