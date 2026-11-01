class BadWord(Exception):
    pass


def sort_in_place(xs: list[int]) -> int:
    xs.sort()
    return len(xs)


def wrong_hint(n: int) -> int:
    return n / 2


def strict_word(w: str) -> int:
    if not w:
        raise BadWord("empty")
    return len(w)


def count_chars(s: str) -> int:
    return len(s)



def total(xs: list[int]) -> int:
    t = 0
    for x in xs:
        t += x * x
    return t

