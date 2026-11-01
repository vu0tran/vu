"""GPS-track helpers as data scripts write them: plain Python with the math module."""
import math

EARTH_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(a))


def track_km(lats: list[float], lons: list[float]) -> float:
    """The length of a track: the sum of the distances between its points, in order."""
    total = 0.0
    for i in range(1, min(len(lats), len(lons))):
        total += haversine_km(lats[i - 1], lons[i - 1], lats[i], lons[i])
    return total


def nearest(lats: list[float], lons: list[float], qlats: list[float], qlons: list[float]) -> list[int]:
    """For each query point, the index of the closest point (the first, when two are as close)."""
    if len(lats) != len(lons) or len(qlats) != len(qlons):
        raise ValueError("latitudes and longitudes must come in pairs")
    out = []
    for qa, qo in zip(qlats, qlons):
        best, best_d = -1, math.inf
        for i in range(len(lats)):
            d = haversine_km(qa, qo, lats[i], lons[i])
            if d < best_d:
                best, best_d = i, d
        out.append(best)
    return out
