"""Edit distance, written in Vu (fuzzy.vu) and called through ctypes."""
import ctypes
import os

_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "libfuzzy.so"))
_lib.distance.restype = ctypes.c_int64
_lib.distance.argtypes = [ctypes.c_char_p, ctypes.c_int64, ctypes.c_char_p, ctypes.c_int64]
_lib.closest.restype = ctypes.c_int64
_lib.closest.argtypes = [ctypes.c_char_p, ctypes.c_int64, ctypes.c_char_p, ctypes.c_int64]


def distance(a: str, b: str) -> int:
    """How many single-character insertions, deletions and substitutions turn a into b."""
    x, y = a.encode(), b.encode()
    return _lib.distance(x, len(x), y, len(y))


def closest(word: str, words: list) -> str:
    """The word of words nearest to word (the first of equals); None when words is empty."""
    if not words:
        return None
    if any("\n" in w for w in words):
        raise ValueError("a word can't contain a line break")
    x, ws = word.encode(), "\n".join(words).encode()
    return words[_lib.closest(x, len(x), ws, len(ws))]
