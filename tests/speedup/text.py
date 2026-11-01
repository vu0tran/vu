import re
from collections import Counter


def word_counts(text: str) -> dict[str, int]:
    return dict(Counter(re.findall(r"\w+", text.lower())))



def minmax(xs: list[int]) -> tuple[int, ...]:
    if not xs:
        raise ValueError("empty")
    return (min(xs), max(xs))



def first_long(words: list[str], n: int | None = None) -> str | None:
    for w in words:
        if len(w) > (n if n is not None else 5):
            return w
    return None



def checksum(data: bytes, odd: bool = False) -> int:
    s = 0
    for i, b in enumerate(data):
        if odd and i % 2 == 0:
            continue
        s = (s * 31 + b) % 1000000007
    return s




def scale(xs: list[float], k: float) -> list[float]:
    return [x * k for x in xs]

